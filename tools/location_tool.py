"""
Location and nearby hospital/lab search tool using OpenStreetMap.
"""
import requests
import json
from typing import List, Dict, Optional

NOMINATIM_API = "https://nominatim.openstreetmap.org/search"
OVERPASS_API = "https://overpass-api.de/api/interpreter"


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
        response = requests.get(NOMINATIM_API, params=params, timeout=10)
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
    try:
        # Overpass query to find hospitals within radius
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="hospital"](around:{radius},{lat},{lon});
          way["amenity"="hospital"](around:{radius},{lat},{lon});
          relation["amenity"="hospital"](around:{radius},{lat},{lon});
        );
        out center;
        """
        
        params = {'data': query}
        response = requests.get(OVERPASS_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        hospitals = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', 'Unknown Hospital')
            
            # Get coordinates
            if 'lat' in element and 'lon' in element:
                hospital_lat = element['lat']
                hospital_lon = element['lon']
            elif 'center' in element:
                hospital_lat = element['center']['lat']
                hospital_lon = element['center']['lon']
            else:
                continue
            
            hospitals.append({
                'name': name,
                'lat': hospital_lat,
                'lon': hospital_lon,
                'address': tags.get('addr:street', ''),
                'phone': tags.get('phone', tags.get('contact:phone', '')),
                'type': 'hospital'
            })
        
        # Limit to top 10 results
        return hospitals[:10]
    except Exception as e:
        print(f"[Location Tool Error] Hospital search failed: {e}")
        return []


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
    try:
        # Overpass query to find diagnostic labs within radius
        query = f"""
        [out:json][timeout:25];
        (
          node["healthcare"="laboratory"](around:{radius},{lat},{lon});
          way["healthcare"="laboratory"](around:{radius},{lat},{lon});
          relation["healthcare"="laboratory"](around:{radius},{lat},{lon});
          node["amenity"="laboratory"](around:{radius},{lat},{lon});
          way["amenity"="laboratory"](around:{radius},{lat},{lon});
          relation["amenity"="laboratory"](around:{radius},{lat},{lon});
        );
        out center;
        """
        
        params = {'data': query}
        response = requests.get(OVERPASS_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        labs = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', 'Unknown Lab')
            
            # Get coordinates
            if 'lat' in element and 'lon' in element:
                lab_lat = element['lat']
                lab_lon = element['lon']
            elif 'center' in element:
                lab_lat = element['center']['lat']
                lab_lon = element['center']['lon']
            else:
                continue
            
            labs.append({
                'name': name,
                'lat': lab_lat,
                'lon': lab_lon,
                'address': tags.get('addr:street', ''),
                'phone': tags.get('phone', tags.get('contact:phone', '')),
                'type': 'laboratory'
            })
        
        # Limit to top 10 results
        return labs[:10]
    except Exception as e:
        print(f"[Location Tool Error] Lab search failed: {e}")
        return []


def get_nearby_medical_facilities(lat: float, lon: float, radius: int = 5000) -> Dict[str, List[Dict[str, str]]]:
    """
    Get both hospitals and labs near a location.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default: 5000m = 5km)
        
    Returns:
        Dictionary with 'hospitals' and 'labs' keys
    """
    hospitals = search_nearby_hospitals(lat, lon, radius)
    labs = search_nearby_labs(lat, lon, radius)
    
    return {
        'hospitals': hospitals,
        'labs': labs
    }
