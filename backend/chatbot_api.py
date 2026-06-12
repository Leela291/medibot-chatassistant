# backend/chatbot_api.py
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from flask import Blueprint, request, jsonify, Response
from memory.session_manager import session_manager
from rag.rag_pipeline import run_rag
from tools.emergency_tool import handle_emergency
from tools.doctor_search_tool import search_doctors, format_doctor_list
from tools.appointment_tool import book_appointment, format_confirmation, get_available_slots
from llm.model_loader import get_model_info
from llm.response_generator import generate_response, generate_with_rag
from backend.file_parser import parse_uploaded_file
from tools.fda_tool import get_fda_drug_summary
from tools.location_tool import get_nearby_medical_facilities, format_nearby_facilities, parse_location_request
from tools.bmi_tool import calculate_bmi

health_bp  = Blueprint("health",  __name__)
chatbot_bp = Blueprint("chatbot", __name__)
admin_bp   = Blueprint("admin",   __name__)

# List of common drug names we check for openFDA lookup
COMMON_DRUGS = [
    "salbutamol", "albuterol", "ventolin", "asthalin",
    "levosalbutamol", "levalbuterol", "xopenex",
    "terbutaline", "bricanyl", "budesonide", "pulmicort", "budecort",
    "fluticasone", "flovent", "beclomethasone", "qvar",
    "mometasone", "asmanex", "ciclesonide", "alvesco",
    "salmeterol", "serevent", "formoterol", "foradil",
    "indacaterol", "onbrez", "montelukast", "singulair", "montair",
    "zafirlukast", "accolate", "prednisolone", "omnacortil", "wysolone",
    "dexamethasone", "dexona", "methylprednisolone", "medrol",
    "omalizumab", "xolair", "mepolizumab", "nucala", "benralizumab",
    "fasenra", "dupilumab", "dupixent", "tezepelumab", "tezspire",
    "theophylline", "ipratropium", "atrovent", "tiotropium", "spiriva",
    "cetirizine", "zyrtec", "cetzine", "loratadine", "claritin",
    "fexofenadine", "allegra", "cromolyn", "epinephrine", "adrenaline",
    "metformin", "insulin", "paracetamol", "acetaminophen", "ibuprofen",
    "aspirin", "amoxicillin", "penicillin", "lipitor", "atorvastatin"
]

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
    stream     = body.get("stream", False)
    
    if not message:
        return jsonify({"error": "message is required"}), 400
        
    session = session_manager.get_or_create(session_id)
    emergency = handle_emergency(message)
    
    if emergency:
        session.memory.add_user(message)
        session.memory.add_assistant(emergency["answer"])
        session_manager.save_session(session)
        if stream:
            def generate_emergency():
                yield f"data: {json.dumps({'session_id': session.session_id, 'is_emergency': True, 'sources': []})}\n\n"
                words = emergency["answer"].split(" ")
                for idx, w in enumerate(words):
                    space = " " if idx < len(words) - 1 else ""
                    yield f"data: {json.dumps({'token': w + space})}\n\n"
            return Response(generate_emergency(), mimetype='text/event-stream')
        return jsonify({"answer": emergency["answer"], "session_id": session.session_id, "is_emergency": True, "sources": []})
    
    # 1. Trigger openFDA summary if a common drug name is detected in query
    fda_context = ""
    detected_drug = None
    for drug in COMMON_DRUGS:
        if drug in message.lower():
            detected_drug = drug
            break
            
    if detected_drug:
        try:
            fda_context = get_fda_drug_summary(detected_drug)
            print(f"[openFDA] Injected official drug label summary for: {detected_drug}")
        except Exception as e:
            print(f"[openFDA Error] Failed to generate drug summary: {e}")

    history = session.memory.get_history()
    
    import re

    if "bmi" in message.lower():
        return jsonify({
            "answer": (
                "Please provide your weight and height.\n\n"
                "Example:\n"
                "70 kg 175 cm"
            ),
            "session_id": session.session_id,
            "sources": ["BMI Calculator"],
            "is_emergency": False
        })

    bmi_pattern = r"(\d+(?:\.\d+)?)\s*kg.*?(\d+(?:\.\d+)?)\s*cm"

    match = re.search(bmi_pattern, message.lower())

    if match:
        weight = float(match.group(1))
        height = float(match.group(2))

        result = calculate_bmi(weight, height)

        answer = (
            f"Your BMI is {result['bmi']}.\n"
            f"Category: {result['category']}"
        )

        session.memory.add_user(message)
        session.memory.add_assistant(answer)
        session_manager.save_session(session)

        return jsonify({"answer": answer, "session_id": session.session_id, "sources": ["BMI Calculator"], "is_emergency": False})

    # 2. Optimized Generation Routing
    if use_rag:
        if fda_context:
            # Manually retrieve to avoid calling the LLM twice!
            from vector_db.retriever import retrieve
            from rag.context_builder import build_context
            
            chunks = retrieve(message)
            db_context = build_context(chunks)
            augmented_query = f"Incorporating official drug information:\n{fda_context}\n\nUser Question: {message}"
            
            answer = generate_with_rag(augmented_query, db_context, history, stream=stream)
            sources = list({c["disease"]["name"] if isinstance(c["disease"], dict) else c.get("disease", "Local Docs") for c in chunks})
            sources.append("openFDA Database")
        else:
            # Standard RAG handles the generation automatically
            result = run_rag(message, history, stream=stream)
            answer = result["answer"]
            sources = result["sources"]
    else:
        if fda_context:
            augmented_query = f"Incorporating official drug information:\n{fda_context}\n\nUser Question: {message}"
            answer = generate_response(augmented_query, history, stream=stream)
            sources = ["openFDA Database"]
        else:
            answer  = generate_response(message, history, stream=stream)
            sources = []
            
    # 3. Stream or Return JSON
    if stream:
        def stream_generator():
            yield f"data: {json.dumps({'session_id': session.session_id, 'sources': sources, 'is_emergency': False})}\n\n"
            
            full_text = []
            for token in answer:
                full_text.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            complete_answer = "".join(full_text)
            session.memory.add_user(message)
            session.memory.add_assistant(complete_answer)
            session_manager.save_session(session)
            
        return Response(stream_generator(), mimetype='text/event-stream')

    session.memory.add_user(message)
    session.memory.add_assistant(answer)
    session_manager.save_session(session) 
    
    return jsonify({"answer": answer, "session_id": session.session_id, "sources": sources, "is_emergency": False})

@chatbot_bp.post("/chat/new")
def new_session():
    session = session_manager.get_or_create()
    return jsonify({"session_id": session.session_id})

@chatbot_bp.post("/location/nearby")
def nearby_medical_facilities():
    body = request.get_json(force=True)
    lat = body.get("lat")
    lon = body.get("lon")
    radius = int(body.get("radius", 5000))
    session_id = body.get("session_id")
    user_query = (body.get("query") or "").strip()

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
        radius = max(1000, min(radius, 15000))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid location coordinates"}), 400

    request_info = parse_location_request(user_query)
    facilities = get_nearby_medical_facilities(
        lat,
        lon,
        radius,
        facility_types=request_info["facility_types"],
        specialty=request_info["specialty"],
    )
    if sum(len(items) for items in facilities.values()) == 0 and radius < 15000:
        radius = 15000
        facilities = get_nearby_medical_facilities(
            lat,
            lon,
            radius,
            facility_types=request_info["facility_types"],
            specialty=request_info["specialty"],
        )

    if not request_info["specialty"]:
        empty_types = [
            facility_type
            for facility_type in request_info["facility_types"]
            if len(facilities.get(facility_type, [])) == 0
        ]
        if empty_types:
            fallback_request = {
                **request_info,
                "facility_types": empty_types,
            }
            fallback_facilities = search_nominatim_medical_places(lat, lon, radius, fallback_request)
            for facility_type, items in fallback_facilities.items():
                if items:
                    facilities[facility_type] = items

    answer = format_nearby_facilities(facilities, lat=lat, lon=lon, radius=radius, request_info=request_info)

    session = session_manager.get_or_create(session_id)
    session.memory.add_user(request_info["display_query"])
    session.memory.add_assistant(answer)
    session_manager.save_session(session)

    return jsonify({
        "answer": answer,
        "facilities": facilities,
        "session_id": session.session_id,
        "sources": ["OpenStreetMap Overpass", "OpenStreetMap Nominatim"],
        "is_emergency": False,
    })

@chatbot_bp.get("/chat/sessions")
def get_sessions():
    """Return all active chat sessions with descriptive titles and timestamps."""
    sessions = []
    for s_id, s in session_manager._sessions.items():
        history = s.memory.get_all_history()
        title = "New Consultation"
        last_msg = ""
        if history:
            user_msgs = [m for m in history if m["role"] == "user"]
            if user_msgs:
                title = user_msgs[0]["content"]
                if title.startswith("[Uploaded:"):
                    title = title.split("]", 1)[-1].strip()
                if len(title) > 32:
                    title = title[:29] + "..."
            last_msg = history[-1]["content"]
            if len(last_msg) > 50:
                last_msg = last_msg[:47] + "..."
        
        sessions.append({
            "session_id": s_id,
            "title": title or "Empty Session",
            "last_message": last_msg or "No messages yet",
            "updated_at": s.updated_at,
        })
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return jsonify({"sessions": sessions})

@chatbot_bp.get("/chat/history")
def get_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    session = session_manager.get_or_create(session_id)
    return jsonify({"history": session.memory.get_all_history()})

@chatbot_bp.delete("/chat/history")
def clear_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    session = session_manager.get_or_create(session_id)
    session.memory.clear()
    session_manager.save_session(session)
    return jsonify({"status": "cleared"})

@chatbot_bp.delete("/chat/session/<session_id>")
def delete_session(session_id):
    """Delete a specific session completely from memory and disk."""
    session_manager.delete(session_id)
    return jsonify({"status": "deleted", "session_id": session_id})

@chatbot_bp.post("/chat/upload")
def chat_with_file():
    """Handle file/image upload + optional message for clinical analysis."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    message = request.form.get("message", "").strip()
    session_id = request.form.get("session_id")

    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    parsed = parse_uploaded_file(file)
    if (
        parsed.get("is_image")
        and not parsed.get("is_document", False)
        and (
            parsed.get("width", 0) < 300
            or parsed.get("height", 0) < 300
        )
    ):
        return jsonify({
            "answer":
                "The uploaded image resolution is too low for reliable analysis. "
                "Please upload the original image or a clearer photo.",
            "session_id": session_id,
            "sources": [],
            "is_emergency": False
        })

    if not parsed["success"] and not parsed["content"]:
        return jsonify({
            "error": parsed["error"] or "Failed to parse file",
            "answer": f"⚠️ Could not process the file: {parsed['error']}",
            "session_id": session_id,
            "sources": [],
            "is_emergency": False,
        })

    session = session_manager.get_or_create(session_id)
    history = session.memory.get_history()
    
    file_context = parsed["content"]
    user_prompt = message or (
    "Analyze this file and provide "
    "diagnosis, danger level, medicines, "
    "diet recommendations and precautions."
    )
    images = [parsed["base64_image"]] if parsed.get("is_image") and parsed.get("base64_image") else None
    print(
    f"[UPLOAD] {parsed['filename']} "
    f"is_image={parsed.get('is_image')} "
    f"base64={parsed.get('base64_image') is not None}"
    )

    if parsed.get("is_image") and not parsed.get("is_document", False):
        # ── Disease Photo Upload prompt ──
        combined_message = f"""
        Analyze the uploaded medical image.
        You are a medical image analysis assistant.

        IMPORTANT RULES:
        - Never provide a definitive diagnosis from an image alone.
        - Rank possible conditions instead of choosing only one diagnosis.
        - If multiple conditions fit the image, list them.
        - Reduce confidence when clinical history is unavailable.
        - Explain uncertainty when appropriate.
        - Do not claim a condition is confirmed.
        - Use phrases like "may be consistent with", "could represent", or "cannot be confirmed from the image alone".
        - Never assign "High" confidence unless the visual findings are highly specific.
        - For generalized rashes, confidence should usually be Low or Medium unless classic diagnostic features are present.
        - Explain why confidence was chosen.
        - Describe the rash pattern before suggesting conditions.
        - If several conditions appear equally plausible, state this clearly.
       
        User question:
        {user_prompt}

        Provide:

        1. Visible Findings
        - Describe exactly what is visible in the image.

        2. Most Likely Possibilities (Ranked)
        - For each possibility include:
        - Confidence (Low/Medium/High)
        - Reasoning based on visible features

        3. Possible Causes
        - Explain common causes of the top possibilities.

        4. Recommended Next Steps
        - Include self-care and monitoring advice when appropriate.

        5. When to See a Doctor
        - Explain when medical evaluation is recommended.

        6. Emergency Warning Signs
        - List symptoms requiring urgent or emergency care.

        7. Limitations
        - Explain what cannot be determined from the image alone.

        8. Information Needed For Better Accuracy
        - List the most important symptoms or history that would improve diagnostic confidence.

        Format the response in clear sections using markdown headings.
        """
    
        if images:
            print("Base64 length:", len(images[0]))
            print("Base64 start:", images[0][:50])
        answer = generate_response(
            combined_message,
            [],
            images=images
        )
        sources = ["Vision Analysis"]
    else:
        # ── Medical Report Upload prompt ──
        combined_message = (
            f"The user uploaded a patient medical record file: {parsed['filename']}\n\n"
            f"--- FILE CONTENT ---\n"
            f"{file_context}\n"
            f"--- END FILE CONTENT ---\n\n"
            f"User's question: {user_prompt}\n\n"
            f"Please perform a rigorous clinical analysis of this medical record and return a structured report answering:\n"
            f"1. **What Disease/Condition it Suggests & Why it Occurs**:Suspected health issues based on the clinical parameters and why they develop.\n"
            f"2. **Danger Level**: Explicitly rate the condition as either [Danger Level: Low], [Danger Level: Medium], [Danger Level: High], or [Danger Level: Emergency] with a clear clinical rationale.\n"
            f"3. **What Medicine We Need to Take**: Outline typical prescription drug classes or OTC medications relevant here (with a warning that exact dosing requires a physician).\n"
            f"4. **How Long it Stays (Expected Recovery)**: Typical duration of this disease/indicator aberration and monitoring timeframe.\n"
            f"5. **What Diet Should be Followed**: What nutritional adjustments are vital (what to eat, what to avoid).\n\n"
            f"Add a clear medical warning disclaimer at the end."
        )

        answer = generate_response(combined_message, history, images=images)
        sources = [f"Medical Report: {parsed['filename']}"]

    session.memory.add_user(f"[Uploaded: {parsed['filename']}] {user_prompt}")
    session.memory.add_assistant(answer)
    session_manager.save_session(session)

    return jsonify({
        "answer": answer,
        "session_id": session.session_id,
        "sources": sources,
        "is_emergency": "[Danger Level: Emergency]" in answer or "[Danger Level: High]" in answer,
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