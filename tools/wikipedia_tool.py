# tools/wikipedia_tool.py
"""
Wikipedia API Integration Tool for MedoAir.
Fetches authoritative summary introductions for medical conditions/diseases
when the local FAISS RAG database does not contain the answer.
This is completely free and requires no API keys.
"""
import requests
import urllib.parse

BASE_URL = "https://en.wikipedia.org/w/api.php"

def search_wikipedia_page(query: str) -> str | None:
    """
    Search Wikipedia for a disease or medical condition.
    Returns the page title of the best match, or None.
    """
    if not query or len(query.strip()) < 3:
        return None

    # Refine queries to prioritize medical definitions if needed
    search_query = query.strip()
    
    params = {
        "action": "query",
        "list": "search",
        "srsearch": search_query,
        "format": "json",
        "limit": 3
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=8)
        if response.status_code != 200:
            return None
            
        data = response.json()
        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            return None
            
        # Prioritize titles that are exact matches or contain the word
        for result in search_results:
            title = result.get("title", "")
            # Avoid disambiguation pages
            if "disambiguation" in title.lower():
                continue
            return title
            
        return search_results[0].get("title")
    except Exception as e:
        print(f"[Wikipedia Search Error] Failed to search Wikipedia: {e}")
        return None


def get_wikipedia_extract(title: str) -> str | None:
    """
    Fetch the introductory summary (extract) of a Wikipedia page.
    """
    if not title:
        return None

    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": "true",
        "explaintext": "true",
        "titles": title,
        "format": "json"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=8)
        if response.status_code != 200:
            return None
            
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id == "-1":
                continue
            extract = page_data.get("extract", "").strip()
            if extract:
                return extract
        return None
    except Exception as e:
        print(f"[Wikipedia Extract Error] Failed to fetch extract for '{title}': {e}")
        return None


def get_wikipedia_disease_summary(disease_name: str) -> str | None:
    """
    Combines search and extract retrieval.
    Returns a formatted block of text suitable for prompt context augmentation.
    """
    print(f"[Wikipedia] Looking up info for: {disease_name}...")
    title = search_wikipedia_page(disease_name)
    if not title:
        # Retry with a stripped version
        words = disease_name.split()
        if len(words) > 1:
            title = search_wikipedia_page(words[-1])
            
    if not title:
        return None
        
    extract = get_wikipedia_extract(title)
    if not extract:
        return None
        
    # Format similarly to RAG dataset context
    summary = (
        f"=== Wikipedia Medical Encyclopedia: {title} ===\n"
        f"Description: {extract}\n"
    )
    return summary
