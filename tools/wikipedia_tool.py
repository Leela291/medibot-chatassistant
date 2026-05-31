# tools/wikipedia_tool.py
import wikipediaapi

def search_wikipedia(query: str, sentences: int = 5) -> dict:
    try:
        wiki = wikipediaapi.Wikipedia(
            language="en",
            user_agent="MediBot/1.0 (medical chatbot)"
        )

        page = wiki.page(query)

        if not page.exists():
            page = wiki.page(query + " disease")

        if not page.exists():
            return {"found": False, "summary": "", "url": ""}

        summary = page.summary
        sentences_list = summary.split(". ")
        short_summary = ". ".join(sentences_list[:sentences]) + "."

        return {
            "found": True,
            "title": page.title,
            "summary": short_summary,
            "url": page.fullurl
        }

    except Exception as e:
        return {"found": False, "summary": "", "url": "", "error": str(e)}


def get_wikipedia_context(disease: str) -> str:
    result = search_wikipedia(disease)
    if result["found"]:
        return f"Wikipedia Information about {result['title']}:\n{result['summary']}\nSource: {result['url']}"
    else:
        return ""