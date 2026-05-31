import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Blueprint, request, jsonify

from memory.session_manager import session_manager
from rag.rag_pipeline import run_rag

from tools.emergency_tool import handle_emergency
from tools.doctor_search_tool import (
    search_doctors,
    format_doctor_list
)
from tools.appointment_tool import (
    book_appointment,
    format_confirmation,
    get_available_slots
)

from llm.model_loader import get_model_info
from llm.response_generator import generate_response

from backend.file_parser import parse_uploaded_file

# NEW
from services.symptom_detector import detect_symptom
from services.triage_questions import TRIAGE_QUESTIONS


health_bp = Blueprint("health", __name__)
chatbot_bp = Blueprint("chatbot", __name__)
admin_bp = Blueprint("admin", __name__)


@health_bp.get("/health")
def health():
    info = get_model_info()

    return jsonify({
        "status": "ok" if info["connected"] else "ollama_offline",
        "model": info["llm_model"],
        "connected": info["connected"]
    })


@chatbot_bp.post("/chat")
def chat():

    body = request.get_json(force=True)

    message = (body.get("message") or "").strip()
    session_id = body.get("session_id")
    use_rag = body.get("use_rag", True)

    if not message:
        return jsonify({"error": "message is required"}), 400

    session = session_manager.get_or_create(session_id)

    # --------------------------------------------------
    # Emergency handling
    # --------------------------------------------------
    emergency = handle_emergency(message)

    if emergency:

        session.memory.add_user(message)
        session.memory.add_assistant(emergency["answer"])

        return jsonify({
            "answer": emergency["answer"],
            "session_id": session.session_id,
            "is_emergency": True,
            "sources": []
        })

    history = session.memory.get_history()

    # --------------------------------------------------
    # Symptom-first flow
    # --------------------------------------------------
    symptom = None

    try:
        symptom = detect_symptom(message)
    except Exception as e:
        print(f"[Symptom Detector Error] {e}")

    if symptom:

        questions = TRIAGE_QUESTIONS.get(symptom, [])

        answer = "I'd like to understand your symptoms better. Please answer the following questions:"

        sources = []
        
        follow_up_questions = questions

    else:

        # --------------------------------------------------
        # Existing RAG flow
        # --------------------------------------------------
        if use_rag:

            result = run_rag(
                message,
                history
            )

            answer = result["answer"]
            sources = result["sources"]

        else:

            answer = generate_response(
                message,
                history
            )

            sources = []
        
        follow_up_questions = []

    session.memory.add_user(message)
    session.memory.add_assistant(answer)

    return jsonify({
        "answer": answer,
        "session_id": session.session_id,
        "sources": sources,
        "is_emergency": False,
        "follow_up_questions": follow_up_questions
    })


@chatbot_bp.post("/chat/new")
def new_session():

    session = session_manager.get_or_create()

    return jsonify({
        "session_id": session.session_id
    })


@chatbot_bp.get("/chat/history")
def get_history():

    session_id = request.args.get("session_id")

    if not session_id:
        return jsonify({
            "error": "session_id required"
        }), 400

    session = session_manager.get_or_create(session_id)

    return jsonify({
        "history": session.memory.get_history()
    })


@chatbot_bp.delete("/chat/history")
def clear_history():

    session_id = request.args.get("session_id")

    if not session_id:
        return jsonify({
            "error": "session_id required"
        }), 400

    session = session_manager.get_or_create(session_id)

    session.memory.clear()

    return jsonify({
        "status": "cleared"
    })


@chatbot_bp.post("/chat/upload")
def chat_with_file():

    if "file" not in request.files:
        return jsonify({
            "error": "No file uploaded"
        }), 400

    file = request.files["file"]

    message = request.form.get("message", "").strip()
    session_id = request.form.get("session_id")

    if not file.filename:
        return jsonify({
            "error": "Empty filename"
        }), 400

    parsed = parse_uploaded_file(file)

    if not parsed["success"] and not parsed["content"]:

        return jsonify({
            "error": parsed["error"] or "Failed to parse file",
            "answer": f"⚠️ Could not process file: {parsed['error']}",
            "session_id": session_id,
            "sources": [],
            "is_emergency": False,
        })

    file_context = parsed["content"]

    user_prompt = (
        message
        or "Please analyze this patient record."
    )

    combined_message = f"""
The user uploaded a patient record.

Filename:
{parsed['filename']}

FILE CONTENT:
{file_context}

User Question:
{user_prompt}

Please provide:

1. Summary of findings
2. Abnormal values
3. Possible conditions
4. Recommended follow-up tests
5. When to consult a doctor
"""

    session = session_manager.get_or_create(session_id)

    history = session.memory.get_history()

    answer = generate_response(
        combined_message,
        history
    )

    session.memory.add_user(
        f"[Uploaded: {parsed['filename']}] {user_prompt}"
    )

    session.memory.add_assistant(answer)

    return jsonify({
        "answer": answer,
        "session_id": session.session_id,
        "sources": [f"Uploaded: {parsed['filename']}"],
        "is_emergency": False
    })


@chatbot_bp.post("/doctors/search")
def doctor_search():

    body = request.get_json(force=True)

    condition = body.get("condition", "general")
    city = body.get("city")

    doctors = search_doctors(
        condition=condition,
        city=city
    )

    return jsonify({
        "doctors": doctors,
        "formatted": format_doctor_list(doctors)
    })


@chatbot_bp.post("/appointments/slots")
def available_slots():

    body = request.get_json(force=True)

    doctor = body.get("doctor_name", "")
    date = body.get("date")

    slots = get_available_slots(
        doctor,
        date
    )

    return jsonify({
        "slots": slots
    })


@chatbot_bp.post("/appointments/book")
def book():

    body = request.get_json(force=True)

    required = [
        "patient_name",
        "doctor_name",
        "date",
        "time_slot"
    ]

    missing = [
        f for f in required
        if not body.get(f)
    ]

    if missing:
        return jsonify({
            "error": f"Missing fields: {', '.join(missing)}"
        }), 400

    appointment = book_appointment(
        patient_name=body["patient_name"],
        doctor_name=body["doctor_name"],
        date=body["date"],
        time_slot=body["time_slot"],
        reason=body.get("reason", "")
    )

    return jsonify({
        "appointment": appointment,
        "confirmation": format_confirmation(appointment)
    })


@admin_bp.post("/rebuild-index")
def rebuild_index():

    try:
        from vector_db.vector_store import build_vector_store

        build_vector_store(
            force_rebuild=True
        )

        return jsonify({
            "status": "index rebuilt successfully"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


@admin_bp.get("/model-info")
def model_info():

    return jsonify(
        get_model_info()
    )