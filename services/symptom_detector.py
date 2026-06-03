# memory/services/symptom_detector.py

SYMPTOMS = [
    "body pain",
    "headache",
    "fever",
    "cough",
    "stomach pain",
    "chest pain",
    "shortness of breath",
    "sore throat"
]

def detect_symptom(text):
    text = text.lower()

    for symptom in SYMPTOMS:
        if symptom in text:
            return symptom

    return None