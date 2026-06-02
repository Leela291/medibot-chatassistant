# tools/wikipedia_tool.py
"""
Fetch summaries from Wikipedia (via wikipedia-api, no API key required).
Extracts meaningful search terms from natural-language user queries.
"""
import re

import wikipediaapi

# Disease / topic names we can pull from free-text queries
KNOWN_TOPICS = [
    "diabetes", "asthma", "dengue", "malaria", "tuberculosis", "typhoid",
    "influenza", "flu", "covid-19", "covid", "common cold", "diarrhea",
    "diarrhoeal", "hyperthyroidism", "hypothyroidism", "pneumonia",
    "stroke", "cancer", "hypertension", "anemia", "hepatitis",
]

# Map symptom words to Wikipedia article titles that usually exist
SYMPTOM_WIKI_TITLES = {
    "fever": "Fever",
    "cough": "Cough",
    "headache": "Headache",
    "diabetes": "Diabetes",
    "asthma": "Asthma",
    "dengue": "Dengue fever",
    "malaria": "Malaria",
    "tuberculosis": "Tuberculosis",
    "typhoid": "Typhoid fever",
    "influenza": "Influenza",
    "flu": "Influenza",
    "covid": "COVID-19",
    "covid-19": "COVID-19",
    "pneumonia": "Pneumonia",
    "nausea": "Nausea",
    "vomiting": "Vomiting",
    "diarrhea": "Diarrhea",
    "rash": "Rash",
    "anemia": "Anemia",
}

FILLER = re.compile(
    r"\b(i|me|my|have|has|had|am|is|are|was|were|the|a|an|and|or|but|"
    r"very|really|please|help|tell|about|what|how|when|why|with|for|"
    r"been|being|feel|feeling|think|getting|get|got|some|any)\b",
    re.IGNORECASE,
)


def extract_wikipedia_queries(user_query: str) -> list[str]:
    """
    Build an ordered list of Wikipedia page titles to try for this message.
    """
    lowered = user_query.lower().strip()
    candidates: list[str] = []

    for topic in sorted(KNOWN_TOPICS, key=len, reverse=True):
        if topic in lowered:
            title = SYMPTOM_WIKI_TITLES.get(topic, topic.title())
            if title not in candidates:
                candidates.append(title)

    for word, title in SYMPTOM_WIKI_TITLES.items():
        if re.search(rf"\b{re.escape(word)}\b", lowered) and title not in candidates:
            candidates.append(title)

    # Cleaned remainder (e.g. "dengue fever treatment" -> "dengue fever treatment")
    cleaned = FILLER.sub(" ", lowered)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned and len(cleaned) >= 3:
        titled = cleaned.title()
        if titled not in candidates:
            candidates.append(titled)

    # Last resort: first few meaningful words
    if not candidates:
        words = [w for w in re.findall(r"[a-z0-9-]+", lowered) if len(w) > 2]
        if words:
            candidates.append(" ".join(words[:4]).title())

    return candidates


def search_wikipedia(query: str, sentences: int = 5) -> dict:
    try:
        wiki = wikipediaapi.Wikipedia(
            language="en",
            user_agent="MediBot/1.0 (medical chatbot; educational use)",
        )

        page = wiki.page(query)

        if not page.exists():
            page = wiki.page(query + " disease")

        if not page.exists():
            return {"found": False, "summary": "", "url": "", "title": query}

        summary = page.summary
        sentences_list = summary.split(". ")
        short_summary = ". ".join(sentences_list[:sentences]) + "."

        return {
            "found": True,
            "title": page.title,
            "summary": short_summary,
            "url": page.fullurl,
        }

    except Exception as e:
        return {
            "found": False,
            "summary": "",
            "url": "",
            "title": query,
            "error": str(e),
        }


def get_wikipedia_context(user_query: str) -> str:
    """
    Try several extracted titles; return the first successful Wikipedia summary.
    """
    for title in extract_wikipedia_queries(user_query):
        result = search_wikipedia(title)
        if result["found"]:
            return (
                f"Wikipedia — {result['title']}:\n"
                f"{result['summary']}\n"
                f"Source: {result['url']}"
            )
    return ""
