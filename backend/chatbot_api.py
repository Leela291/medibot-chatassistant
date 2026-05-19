# backend/chatbot_api.py
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Blueprint, request, jsonify
from memory.session_manager import session_manager
from rag.rag_pipeline import run_rag
from tools.emergency_tool import handle_emergency
from tools.doctor_search_tool import search_doctors, format_doctor_list
from tools.appointment_tool import book_appointment, format_confirmation, get_available_slots
from llm.model_loader import get_model_info
from llm.response_generator import generate_response
from backend.file_parser import parse_uploaded_file

health_bp  = Blueprint("health",  __name__)
chatbot_bp = Blueprint("chatbot", __name__)
admin_bp   = Blueprint("admin",   __name__)

@health_bp.get("/health")
def health():
    info = get_model_info()
    return jsonify({"status": "ok" if info["connected"] else "ollama_offline", "model": info["llm_model"], "connected": info["connected"]})

@chatbot_bp.post("/chat")
def chat():
    body       = request.get_json(force=True)
    message    = (body.get("message") or "").strip()
    session_id = body.get("session_id")
    use_rag    = body.get("use_rag", True)
    if not message:
        return jsonify({"error": "message is required"}), 400
    session = session_manager.get_or_create(session_id)
    emergency = handle_emergency(message)
    if emergency:
        session.memory.add_user(message)
        session.memory.add_assistant(emergency["answer"])
        return jsonify({"answer": emergency["answer"], "session_id": session.session_id, "is_emergency": True, "sources": []})
    history = session.memory.get_history()
    if use_rag:
        result = run_rag(message, history)
        answer = result["answer"]
        sources = result["sources"]
    else:
        answer  = generate_response(message, history)
        sources = []
    session.memory.add_user(message)
    session.memory.add_assistant(answer)
    return jsonify({"answer": answer, "session_id": session.session_id, "sources": sources, "is_emergency": False})

@chatbot_bp.post("/chat/new")
def new_session():
    session = session_manager.get_or_create()
    return jsonify({"session_id": session.session_id})

@chatbot_bp.get("/chat/history")
def get_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    session = session_manager.get_or_create(session_id)
    return jsonify({"history": session.memory.get_history()})

@chatbot_bp.delete("/chat/history")
def clear_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    session = session_manager.get_or_create(session_id)
    session.memory.clear()
    return jsonify({"status": "cleared"})

@chatbot_bp.post("/chat/upload")
def chat_with_file():
    """Handle file upload + optional message for patient record analysis."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    message = request.form.get("message", "").strip()
    session_id = request.form.get("session_id")

    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Parse the uploaded file
    parsed = parse_uploaded_file(file)

    if not parsed["success"] and not parsed["content"]:
        return jsonify({
            "error": parsed["error"] or "Failed to parse file",
            "answer": f"⚠️ Could not process the file: {parsed['error']}",
            "session_id": session_id,
            "sources": [],
            "is_emergency": False,
        })

    # Build a prompt combining the file content with the user's question
    file_context = parsed["content"]
    user_prompt = message or "Please analyze this patient record and provide insights."

    combined_message = (
        f"The user uploaded a patient record file: {parsed['filename']}\n\n"
        f"--- FILE CONTENT ---\n"
        f"{file_context}\n"
        f"--- END FILE CONTENT ---\n\n"
        f"User's question: {user_prompt}\n\n"
        f"Please analyze this medical data and provide:\n"
        f"1. A summary of key findings from the record\n"
        f"2. Any abnormal values or concerning indicators\n"
        f"3. Possible health conditions these results may suggest\n"
        f"4. Recommended next steps or follow-up tests\n"
        f"5. Important disclaimer about consulting a doctor\n"
    )

    # Get or create session
    session = session_manager.get_or_create(session_id)
    history = session.memory.get_history()

    # Generate response using LLM (without RAG since file content IS the context)
    answer = generate_response(combined_message, history)

    # Store in session memory
    session.memory.add_user(f"[Uploaded: {parsed['filename']}] {user_prompt}")
    session.memory.add_assistant(answer)

    return jsonify({
        "answer": answer,
        "session_id": session.session_id,
        "sources": [f"Uploaded: {parsed['filename']}"],
        "is_emergency": False,
    })

@chatbot_bp.post("/doctors/search")
def doctor_search():
    body      = request.get_json(force=True)
    condition = body.get("condition", "general")
    city      = body.get("city")
    doctors   = search_doctors(condition=condition, city=city)
    return jsonify({"doctors": doctors, "formatted": format_doctor_list(doctors)})

@chatbot_bp.post("/appointments/slots")
def available_slots():
    body   = request.get_json(force=True)
    doctor = body.get("doctor_name", "")
    date   = body.get("date")
    slots  = get_available_slots(doctor, date)
    return jsonify({"slots": slots})

@chatbot_bp.post("/appointments/book")
def book():
    body = request.get_json(force=True)
    required = ["patient_name", "doctor_name", "date", "time_slot"]
    missing  = [f for f in required if not body.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    appt = book_appointment(patient_name=body["patient_name"], doctor_name=body["doctor_name"], date=body["date"], time_slot=body["time_slot"], reason=body.get("reason", ""))
    return jsonify({"appointment": appt, "confirmation": format_confirmation(appt)})

@admin_bp.post("/rebuild-index")
def rebuild_index():
    try:
        from vector_db.vector_store import build_vector_store
        build_vector_store(force_rebuild=True)
        return jsonify({"status": "index rebuilt successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.get("/model-info")
def model_info():
    return jsonify(get_model_info())