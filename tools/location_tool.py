"""
Location and nearby medical facility search tool using OpenStreetMap.
"""
import requests
import json
import re
from typing import List, Dict, Optional
from math import radians, sin, cos, sqrt, atan2

NOMINATIM_API = "https://nominatim.openstreetmap.org/search"
OVERPASS_API = "https://overpass-api.de/api/interpreter"
REQUEST_HEADERS = {
    "User-Agent": "MedoAir-Medical-Assistant/1.0"
}

SPECIALTY_KEYWORDS = {
    "cardiology": ["cardiology", "cardiologist", "heart", "cardiac"],
    "dermatology": ["dermatology", "dermatologist", "skin"],
    "orthopedics": ["orthopedic", "orthopedics", "orthopaedic", "bone", "joint"],
    "gynecology": ["gynecology", "gynaecology", "gynecologist", "gynaecologist", "women"],
    "pediatrics": ["pediatric", "paediatric", "pediatrician", "paediatrician", "child"],
    "neurology": ["neurology", "neurologist", "brain", "nerve"],
    "dentistry": ["dentist", "dental", "dentistry"],
    "ophthalmology": ["eye", "ophthalmology", "ophthalmologist"],
    "ent": ["ent", "ear", "nose", "throat"],
}

FACILITY_SEARCH_TERMS = {
    "hospitals": "hospital",
    "clinics": "clinic",
    "labs": "diagnostic lab",
    "pharmacies": "pharmacy",
    "emergency": "emergency hospital",
}


def _contains_keyword(query: str, keyword: str) -> bool:
    """Match keyword as a full word/phrase so 'nearby' does not trigger 'ear'."""
    return re.search(rf'(?<!\w){re.escape(keyword)}(?!\w)', query) is not None


def parse_location_request(user_query: str = "") -> Dict[str, object]:
    """Infer requested facility categories and specialty from the user's location prompt."""
    query = (user_query or "").lower()
    selected_types = []

    type_keywords = {
        "hospitals": ["hospital", "hospitals"],
        "clinics": ["clinic", "clinics", "doctor", "doctors"],
        "labs": ["lab", "labs", "laboratory", "diagnostic", "test center", "blood test"],
        "pharmacies": ["pharmacy", "pharmacies", "chemist", "medical store", "medicine shop"],
        "emergency": ["emergency", "ambulance", "urgent care", "casualty"],
    }

    for facility_key, keywords in type_keywords.items():
        if any(_contains_keyword(query, keyword) for keyword in keywords):
            selected_types.append(facility_key)

    if not selected_types:
        selected_types = list(FACILITY_TYPES.keys())

    specialty = None
    for specialty_key, keywords in SPECIALTY_KEYWORDS.items():
        if any(_contains_keyword(query, keyword) for keyword in keywords):
            specialty = specialty_key
            break

    display_query = user_query.strip() or "nearby medical facilities"
    return {
        "facility_types": selected_types,
        "specialty": specialty,
        "display_query": display_query,
    }


def get_coordinates_from_address(address: str) -> Optional[Dict[str, float]]:
    """
    Get latitude and longitude from an address using Nominatim.
    
    Args:
        address: The address to geocode
        
    Returns:
        Dictionary with 'lat' and 'lon' keys, or None if failed
    """
    try:
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        response = requests.get(NOMINATIM_API, params=params, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon'])
            }
        return None
    except Exception as e:
        print(f"[Location Tool Error] Geocoding failed: {e}")
        return None


FACILITY_TYPES = {
    "hospitals": {
        "label": "Hospitals",
        "fallback_name": "Unknown Hospital",
        "osm_filters": [
            ('amenity', 'hospital'),
            ('healthcare', 'hospital'),
        ],
    },
    "clinics": {
        "label": "Clinics",
        "fallback_name": "Unknown Clinic",
        "osm_filters": [
            ('amenity', 'clinic'),
            ('healthcare', 'clinic'),
            ('healthcare', 'doctor'),
        ],
    },
    "labs": {
        "label": "Labs",
        "fallback_name": "Unknown Lab",
        "osm_filters": [
            ('healthcare', 'laboratory'),
            ('amenity', 'laboratory'),
        ],
    },
    "pharmacies": {
        "label": "Pharmacies",
        "fallback_name": "Unknown Pharmacy",
        "osm_filters": [
            ('amenity', 'pharmacy'),
            ('healthcare', 'pharmacy'),
        ],
    },
    "emergency": {
        "label": "Emergency Care",
        "fallback_name": "Unknown Emergency Care",
        "osm_filters": [
            ('emergency', 'ambulance_station'),
            ('emergency', 'emergency_ward_entrance'),
            ('emergency', 'yes'),
            ('amenity', 'hospital'),
            ('healthcare', 'hospital'),
            ('healthcare:speciality', 'emergency'),
        ],
    },
}


def calculate_distance_km(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> float:
    """Calculate straight-line distance between two coordinates."""
    earth_radius_km = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [origin_lat, origin_lon, dest_lat, dest_lon])
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return earth_radius_km * 2 * atan2(sqrt(a), sqrt(1 - a))


def _viewbox_for_radius(lat: float, lon: float, radius: int) -> str:
    lat_delta = radius / 111320
    lon_delta = radius / (111320 * max(cos(radians(lat)), 0.1))
    left = lon - lon_delta
    right = lon + lon_delta
    top = lat + lat_delta
    bottom = lat - lat_delta
    return f"{left},{top},{right},{bottom}"


def _build_overpass_query(lat: float, lon: float, radius: int, osm_filters: List[tuple], specialty: Optional[str] = None) -> str:
    selectors = []
    for key, value in osm_filters:
        if specialty:
            selectors.extend([
                f'node["{key}"="{value}"]["healthcare:speciality"~"{specialty}",i](around:{radius},{lat},{lon});',
                f'way["{key}"="{value}"]["healthcare:speciality"~"{specialty}",i](around:{radius},{lat},{lon});',
                f'relation["{key}"="{value}"]["healthcare:speciality"~"{specialty}",i](around:{radius},{lat},{lon});',
                f'node["{key}"="{value}"]["speciality"~"{specialty}",i](around:{radius},{lat},{lon});',
                f'way["{key}"="{value}"]["speciality"~"{specialty}",i](around:{radius},{lat},{lon});',
                f'relation["{key}"="{value}"]["speciality"~"{specialty}",i](around:{radius},{lat},{lon});',
            ])
        else:
            selectors.extend([
                f'node["{key}"="{value}"](around:{radius},{lat},{lon});',
                f'way["{key}"="{value}"](around:{radius},{lat},{lon});',
                f'relation["{key}"="{value}"](around:{radius},{lat},{lon});',
            ])

    return f"""
    [out:json][timeout:25];
    (
      {' '.join(selectors)}
    );
    out center;
    """


def _format_address(tags: Dict[str, str]) -> str:
    parts = [
        tags.get('addr:housenumber', ''),
        tags.get('addr:street', ''),
        tags.get('addr:suburb', ''),
        tags.get('addr:city', ''),
        tags.get('addr:postcode', ''),
    ]
    return ", ".join([part for part in parts if part])


def search_nearby_facilities(
    lat: float,
    lon: float,
    facility_key: str,
    radius: int = 5000,
    limit: int = 8,
    specialty: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Search for a specific medical facility category using OpenStreetMap Overpass API.
    """
    config = FACILITY_TYPES.get(facility_key)
    if not config:
        return []

    try:
        query = _build_overpass_query(lat, lon, radius, config["osm_filters"], specialty=specialty)
        response = requests.get(OVERPASS_API, params={'data': query}, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        facilities = []
        seen = set()
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', config["fallback_name"])

            if 'lat' in element and 'lon' in element:
                facility_lat = element['lat']
                facility_lon = element['lon']
            elif 'center' in element:
                facility_lat = element['center']['lat']
                facility_lon = element['center']['lon']
            else:
                continue

            dedupe_key = (name.lower(), round(float(facility_lat), 5), round(float(facility_lon), 5))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            facilities.append({
                'name': name,
                'lat': facility_lat,
                'lon': facility_lon,
                'address': _format_address(tags),
                'phone': tags.get('phone', tags.get('contact:phone', '')),
                'website': tags.get('website', tags.get('contact:website', '')),
                'type': facility_key,
                'distance_km': round(calculate_distance_km(lat, lon, float(facility_lat), float(facility_lon)), 2),
            })

        facilities.sort(key=lambda item: item['distance_km'])
        return facilities[:limit]
    except Exception as e:
        print(f"[Location Tool Error] {config['label']} search failed: {e}")
        return []


def search_nominatim_medical_places(
    lat: float,
    lon: float,
    radius: int,
    request_info: Dict[str, object],
    limit: int = 8
) -> Dict[str, List[Dict[str, str]]]:
    """
    Free/no-key fallback search using OpenStreetMap Nominatim.
    Useful when Overpass has no specialty-tagged results.
    """
    specialty = request_info.get("specialty")
    requested_types = request_info.get("facility_types") or list(FACILITY_TYPES.keys())
    viewbox = _viewbox_for_radius(lat, lon, radius)
    results = {facility_key: [] for facility_key in requested_types if facility_key in FACILITY_TYPES}

    for facility_key in results:
        term = FACILITY_SEARCH_TERMS.get(facility_key, FACILITY_TYPES[facility_key]["label"])
        query = f"{specialty} {term}" if specialty else term

        try:
            params = {
                "q": query,
                "format": "jsonv2",
                "limit": limit,
                "addressdetails": 1,
                "extratags": 1,
                "viewbox": viewbox,
                "bounded": 1,
            }
            response = requests.get(NOMINATIM_API, params=params, headers=REQUEST_HEADERS, timeout=12)
            response.raise_for_status()
            data = response.json()

            seen = set()
            for place in data:
                place_lat = float(place["lat"])
                place_lon = float(place["lon"])
                distance_km = round(calculate_distance_km(lat, lon, place_lat, place_lon), 2)
                if distance_km > radius / 1000:
                    continue

                name = place.get("name") or place.get("display_name", "").split(",", 1)[0]
                dedupe_key = (name.lower(), round(place_lat, 5), round(place_lon, 5))
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                results[facility_key].append({
                    "name": name or FACILITY_TYPES[facility_key]["fallback_name"],
                    "lat": place_lat,
                    "lon": place_lon,
                    "address": place.get("display_name", ""),
                    "phone": "",
                    "website": "",
                    "type": facility_key,
                    "distance_km": distance_km,
                    "source": "nominatim",
                })

            results[facility_key].sort(key=lambda item: item["distance_km"])
            results[facility_key] = results[facility_key][:limit]
        except Exception as e:
            print(f"[Location Tool Error] Nominatim {facility_key} search failed: {e}")

    return results


def search_nearby_hospitals(lat: float, lon: float, radius: int = 5000) -> List[Dict[str, str]]:
    """
    Search for nearby hospitals using OpenStreetMap Overpass API.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default: 5000m = 5km)
        
    Returns:
        List of hospital information dictionaries
    """
    return search_nearby_facilities(lat, lon, "hospitals", radius, limit=10)


def search_nearby_labs(lat: float, lon: float, radius: int = 5000) -> List[Dict[str, str]]:
    """
    Search for nearby diagnostic labs using OpenStreetMap Overpass API.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default: 5000m = 5km)
        
    Returns:
        List of lab information dictionaries
    """
    return search_nearby_facilities(lat, lon, "labs", radius, limit=10)


def get_nearby_medical_facilities(
    lat: float,
    lon: float,
    radius: int = 5000,
    facility_types: Optional[List[str]] = None,
    specialty: Optional[str] = None
) -> Dict[str, List[Dict[str, str]]]:
    """
    Get medical facilities near a location.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default: 5000m = 5km)
        
    Returns:
        Dictionary grouped by facility type
    """
    requested_types = facility_types or list(FACILITY_TYPES.keys())
    return {
        facility_key: search_nearby_facilities(lat, lon, facility_key, radius, specialty=specialty)
        for facility_key in requested_types
        if facility_key in FACILITY_TYPES
    }


def format_nearby_facilities(
    facilities: Dict[str, List[Dict[str, str]]],
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: int = 5000,
    request_info: Optional[Dict[str, object]] = None
) -> str:
    """Create a chat-friendly summary of nearby medical facilities."""
    request_info = request_info or {}
    radius_km = round(radius / 1000)
    display_query = request_info.get("display_query") or "nearby medical facilities"
    specialty = request_info.get("specialty")
    requested_types = request_info.get("facility_types") or list(FACILITY_TYPES.keys())
    lines = [f"**Results for: {display_query}**", f"Search radius: about {radius_km} km"]
    total = sum(len(items) for items in facilities.values())
    if specialty and total > 0:
        lines.append(f"Showing only facilities tagged with {specialty} in OpenStreetMap.")

    if total == 0:
        if lat is not None and lon is not None:
            searches = {}
            for facility_key in requested_types:
                config = FACILITY_TYPES.get(facility_key)
                if not config:
                    continue
                label = config["label"]
                if specialty:
                    query = f"{specialty} {label.lower()} near me"
                else:
                    query = f"{label.lower()} near me"
                searches[label] = query

            if specialty:
                lines.append(
                    f"\nNo verified {specialty}-specific facility records were found in OpenStreetMap for this area."
                )
                lines.append("Use these map searches to verify directly before visiting:")
            else:
                lines.append("\nOpenStreetMap did not return mapped facilities for this exact area right now.")
                lines.append("Use these location-based searches instead:")
            for label, query in searches.items():
                maps_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}/@{lat},{lon},14z"
                lines.append(f"- [{label}]({maps_url})")
            lines.append("\nFor a medical emergency, call your local emergency number immediately.")
            return "\n".join(lines)

        return (
            "I could not find nearby medical facilities for this location right now. "
            "Please try again, increase the search radius, or search manually in Maps."
        )

    for facility_key in requested_types:
        config = FACILITY_TYPES.get(facility_key)
        if not config:
            continue
        items = facilities.get(facility_key, [])
        lines.append(f"\n**{config['label']}**")
        if not items:
            lines.append("No nearby results found.")
            continue

        for item in items[:5]:
            maps_url = f"https://www.google.com/maps/search/?api=1&query={item['lat']},{item['lon']}"
            details = [f"{item['distance_km']} km away"]
            if item.get('address'):
                details.append(item['address'])
            if item.get('phone'):
                details.append(f"Phone: {item['phone']}")
            verified_label = f" - tagged as {specialty}" if specialty else ""
            lines.append(f"- [{item['name']}]({maps_url}) - {' | '.join(details)}{verified_label}")

    lines.append("\nFor a medical emergency, call your local emergency number immediately.")
    return "\n".join(lines)