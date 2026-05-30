# tools/fda_tool.py
"""
openFDA API Integration Tool for MedoAir.
Fetches official drug label data, clinical adverse event trends, 
and drug recall safety logs to provide authoritative medical data.
"""
import requests
import urllib.parse
from llm.config import OPENFDA_API_KEY

BASE_URL = "https://api.fda.gov"


def query_fda_api(endpoint: str, params: dict) -> dict | None:
    """Helper to query the openFDA API with the loaded API key."""
    # Ensure api_key is added to params
    request_params = params.copy()
    if OPENFDA_API_KEY:
        request_params["api_key"] = OPENFDA_API_KEY

    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=request_params, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            # Not found is a valid api state, just return None
            return None
        else:
            print(f"[openFDA Warning] Received status code {response.status_code} from {url}")
            return None
    except Exception as e:
        print(f"[openFDA Error] Request failed: {e}")
        return None


def search_drug_label(drug_name: str) -> dict | None:
    """
    Search for a drug's official FDA label information.
    Returns dosage, warnings, active ingredients, and indications.
    """
    if not drug_name or len(drug_name.strip()) < 2:
        return None

    drug_name = drug_name.strip()
    # Build clean query searching brand name, generic name or active ingredient
    escaped_name = urllib.parse.quote(f'"{drug_name}"')
    query = f'openfda.brand_name:{escaped_name}+openfda.generic_name:{escaped_name}+active_ingredient:{escaped_name}'
    
    params = {
        "search": query,
        "limit": 1
    }
    
    result = query_fda_api("drug/label.json", params)
    
    # Fallback to general search if specific fields yielded nothing
    if not result:
        params = {
            "search": escaped_name,
            "limit": 1
        }
        result = query_fda_api("drug/label.json", params)

    if not result or "results" not in result or not result["results"]:
        return None

    label = result["results"][0]
    openfda = label.get("openfda", {})

    # Extract useful information cleanly
    return {
        "brand_name": openfda.get("brand_name", [drug_name.capitalize()])[0],
        "generic_name": openfda.get("generic_name", ["N/A"])[0],
        "active_ingredient": label.get("active_ingredient", ["Not listed"])[0] if isinstance(label.get("active_ingredient"), list) else label.get("active_ingredient", "Not listed"),
        "purpose": label.get("purpose", ["N/A"])[0] if isinstance(label.get("purpose"), list) else label.get("purpose", "N/A"),
        "indications_and_usage": label.get("indications_and_usage", ["N/A"])[0] if isinstance(label.get("indications_and_usage"), list) else label.get("indications_and_usage", "N/A"),
        "warnings": label.get("warnings", ["N/A"])[0] if isinstance(label.get("warnings"), list) else label.get("warnings", "N/A"),
        "dosage_and_administration": label.get("dosage_and_administration", ["N/A"])[0] if isinstance(label.get("dosage_and_administration"), list) else label.get("dosage_and_administration", "N/A"),
        "adverse_reactions": label.get("adverse_reactions", ["N/A"])[0] if isinstance(label.get("adverse_reactions"), list) else label.get("adverse_reactions", "N/A"),
    }


def search_drug_adverse_events(drug_name: str, limit: int = 5) -> list[dict] | None:
    """
    Get top clinical reported side-effects / adverse event counts for a drug.
    """
    if not drug_name:
        return None
        
    escaped_name = urllib.parse.quote(f'"{drug_name}"')
    params = {
        "search": f'patient.drug.medicinalproduct:{escaped_name}',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": limit
    }
    
    result = query_fda_api("drug/event.json", params)
    if not result or "results" not in result:
        return None
        
    return result["results"]  # list of {"term": ..., "count": ...}


def search_drug_recalls(drug_name: str, limit: int = 2) -> list[dict] | None:
    """
    Get FDA recall log / enforcement trends for the drug.
    """
    if not drug_name:
        return None
        
    escaped_name = urllib.parse.quote(f'"{drug_name}"')
    params = {
        "search": f'product_description:{escaped_name}+openfda.brand_name:{escaped_name}',
        "limit": limit
    }
    
    result = query_fda_api("drug/enforcement.json", params)
    if not result or "results" not in result:
        return None
        
    recalls = []
    for item in result["results"]:
        recalls.append({
            "recall_number": item.get("recall_number", "N/A"),
            "recalling_firm": item.get("recalling_firm", "N/A"),
            "reason_for_recall": item.get("reason_for_recall", "N/A"),
            "status": item.get("status", "N/A"),
            "recall_initiation_date": item.get("recall_initiation_date", "N/A"),
        })
    return recalls


def get_fda_drug_summary(drug_name: str) -> str:
    """
    Aggregates all openFDA searches into a single clean summary for LLM context.
    """
    label = search_drug_label(drug_name)
    if not label:
        return f"Could not find official openFDA drug label information for '{drug_name}'."

    summary_lines = []
    summary_lines.append(f"=== OFFICIAL FDA DRUG INFO: {label['brand_name']} ({label['generic_name']}) ===")
    summary_lines.append(f"• Active Ingredient: {label['active_ingredient']}")
    summary_lines.append(f"• Purpose: {label['purpose']}")
    summary_lines.append(f"• Indications & Usage: {label['indications_and_usage']}")
    summary_lines.append(f"• Dosage & Administration: {label['dosage_and_administration']}")
    summary_lines.append(f"• Warnings & Precautions: {label['warnings']}")
    summary_lines.append(f"• Adverse Reactions: {label['adverse_reactions']}")

    events = search_drug_adverse_events(drug_name)
    if events:
        summary_lines.append("\n=== HISTORICAL CLINICAL ADVERSE EVENTS (TRENDS) ===")
        summary_lines.append("Most commonly reported reactions by healthcare providers:")
        for idx, event in enumerate(events):
            summary_lines.append(f"  {idx+1}. {event['term']} (Reported Cases: {event['count']})")

    recalls = search_drug_recalls(drug_name)
    if recalls:
        summary_lines.append("\n=== RECENT ENFORCEMENT & SAFETY RECALL LOGS ===")
        for idx, recall in enumerate(recalls):
            summary_lines.append(f"  • Firm: {recall['recalling_firm']}")
            summary_lines.append(f"    Reason: {recall['reason_for_recall']}")
            summary_lines.append(f"    Status: {recall['status']} (Date: {recall['recall_initiation_date']})")
    else:
        summary_lines.append("\n=== SAFETY RECALL LOGS ===")
        summary_lines.append("  No active or historical recalls found for this drug in recent logs.")

    return "\n".join(summary_lines)
