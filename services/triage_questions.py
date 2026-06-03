# memory/services/triage_questions.py

TRIAGE_QUESTIONS = {
    "body pain": [
        {
            "id": "duration",
            "question": "How long have you had the body pain?",
            "type": "radio",
            "options": ["Less than 24 hours", "1-3 days", "4-7 days", "More than a week"]
        },
        {
            "id": "location",
            "question": "Which part of the body hurts the most?",
            "type": "radio",
            "options": ["Back", "Legs", "Arms", "Chest", "Abdomen", "All over"]
        },
        {
            "id": "fever",
            "question": "Do you have fever?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "weakness",
            "question": "Do you feel tired or weak?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "severity",
            "question": "How would you rate the pain severity?",
            "type": "radio",
            "options": ["Mild", "Moderate", "Severe"]
        },
        {
            "id": "physical_activity",
            "question": "Have you recently done heavy physical work or exercise?",
            "type": "radio",
            "options": ["Yes", "No"]
        }
    ],

    "headache": [
        {
            "id": "duration",
            "question": "How long have you had the headache?",
            "type": "radio",
            "options": ["Less than 24 hours", "1-3 days", "4-7 days", "More than a week"]
        },
        {
            "id": "location",
            "question": "Is the pain on one side or both sides of the head?",
            "type": "radio",
            "options": ["One side", "Both sides", "Behind eyes", "Back of head"]
        },
        {
            "id": "fever",
            "question": "Do you have fever?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "nausea",
            "question": "Do you feel nauseous or have vomiting?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "light_sensitivity",
            "question": "Are you sensitive to bright light?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "history",
            "question": "Have you had similar headaches before?",
            "type": "radio",
            "options": ["Yes, frequently", "Yes, occasionally", "No, this is new"]
        }
    ],

    "fever": [
        {
            "id": "temperature",
            "question": "What is your current temperature?",
            "type": "radio",
            "options": ["Below 99°F (37°C)", "99-100°F (37-38°C)", "100-102°F (38-39°C)", "Above 102°F (39°C)"]
        },
        {
            "id": "duration",
            "question": "How many days have you had fever?",
            "type": "radio",
            "options": ["Less than 24 hours", "1-3 days", "4-7 days", "More than a week"]
        },
        {
            "id": "chills",
            "question": "Do you have chills?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "cough",
            "question": "Do you have cough?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "body_pain",
            "question": "Do you have body pain?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "travel",
            "question": "Have you traveled recently?",
            "type": "radio",
            "options": ["Yes, internationally", "Yes, domestically", "No"]
        }
    ],

    "cough": [
        {
            "id": "duration",
            "question": "How long have you had the cough?",
            "type": "radio",
            "options": ["Less than 24 hours", "1-3 days", "4-7 days", "More than a week", "More than 2 weeks"]
        },
        {
            "id": "type",
            "question": "Is it dry or with mucus?",
            "type": "radio",
            "options": ["Dry", "With mucus", "Both"]
        },
        {
            "id": "fever",
            "question": "Do you have fever?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "breath",
            "question": "Do you have shortness of breath?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "chest_pain",
            "question": "Do you have chest pain?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "smoking",
            "question": "Do you smoke?",
            "type": "radio",
            "options": ["Yes", "No", "Former smoker"]
        }
    ],

    "stomach pain": [
        {
            "id": "location",
            "question": "Where exactly is the pain located?",
            "type": "radio",
            "options": ["Upper abdomen", "Lower abdomen", "Right side", "Left side", "Center"]
        },
        {
            "id": "duration",
            "question": "How long have you had the pain?",
            "type": "radio",
            "options": ["Less than 24 hours", "1-3 days", "4-7 days", "More than a week"]
        },
        {
            "id": "nausea",
            "question": "Do you have nausea or vomiting?",
            "type": "radio",
            "options": ["Yes, both", "Nausea only", "Vomiting only", "No"]
        },
        {
            "id": "diarrhea",
            "question": "Do you have diarrhea?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "fever",
            "question": "Do you have fever?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "eating",
            "question": "Does eating make the pain better or worse?",
            "type": "radio",
            "options": ["Better", "Worse", "No change"]
        }
    ],

    "chest pain": [
        {
            "id": "onset",
            "question": "When did the chest pain start?",
            "type": "radio",
            "options": ["Less than 1 hour ago", "1-24 hours ago", "1-3 days ago", "More than 3 days ago"]
        },
        {
            "id": "type",
            "question": "Is the pain sharp, dull, or pressure-like?",
            "type": "radio",
            "options": ["Sharp/stabbing", "Dull/aching", "Pressure/squeezing", "Burning"]
        },
        {
            "id": "breath",
            "question": "Do you have shortness of breath?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "radiation",
            "question": "Does the pain spread to your arm, jaw, or back?",
            "type": "checkbox",
            "options": ["Left arm", "Right arm", "Jaw", "Back", "Neck", "None of these"]
        },
        {
            "id": "dizziness",
            "question": "Do you feel dizzy?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "activity",
            "question": "Does activity make it worse?",
            "type": "radio",
            "options": ["Yes", "No", "Not sure"]
        }
    ],

    "shortness of breath": [
        {
            "id": "onset",
            "question": "When did it start?",
            "type": "radio",
            "options": ["Less than 24 hours", "1-3 days", "4-7 days", "More than a week", "Gradual over time"]
        },
        {
            "id": "timing",
            "question": "Does it occur at rest or during activity?",
            "type": "radio",
            "options": ["At rest only", "During activity only", "Both rest and activity"]
        },
        {
            "id": "chest_pain",
            "question": "Do you have chest pain?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "fever",
            "question": "Do you have fever?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "cough",
            "question": "Do you have a cough?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "asthma",
            "question": "Do you have any history of asthma?",
            "type": "radio",
            "options": ["Yes, diagnosed", "Suspected but not diagnosed", "No"]
        }
    ],

    "sore throat": [
        {
            "id": "duration",
            "question": "How long have you had the sore throat?",
            "type": "radio",
            "options": ["Less than 24 hours", "1-3 days", "4-7 days", "More than a week"]
        },
        {
            "id": "fever",
            "question": "Do you have fever?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "cough",
            "question": "Do you have cough?",
            "type": "radio",
            "options": ["Yes", "No"]
        },
        {
            "id": "swallowing",
            "question": "Is swallowing painful?",
            "type": "radio",
            "options": ["Yes, very painful", "Yes, mildly painful", "No"]
        },
        {
            "id": "glands",
            "question": "Do you have swollen neck glands?",
            "type": "radio",
            "options": ["Yes", "No", "Not sure"]
        },
        {
            "id": "exposure",
            "question": "Have you been around anyone sick recently?",
            "type": "radio",
            "options": ["Yes", "No", "Not sure"]
        }
    ]
}


def get_questions(symptom):
    """
    Return follow-up questions for a symptom.
    """
    symptom = symptom.lower().strip()
    return TRIAGE_QUESTIONS.get(symptom, [])