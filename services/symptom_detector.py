# memory/services/symptom_detector.py

SYMPTOMS = [
    "fever",
    "cough",
    "cold",
    "headache",
    "migraine",
    "body pain",
    "fatigue",
    "weakness",
    "vomiting",
    "nausea",
    "diarrhea",
    "constipation",
    "stomach pain",
    "abdominal pain",
    "chest pain",
    "shortness of breath",
    "sore throat",
    "rash",
    "joint pain",
    "dizziness",
    "loss of smell",
    "loss of taste"
]

def detect_symptom(text):
    text = text.lower()

    for symptom in SYMPTOMS:
        if symptom in text:
            return symptom

    return None