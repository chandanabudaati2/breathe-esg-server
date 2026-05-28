import math

from .models import Airport

# Memory cache for airport coordinate lookups to maximize performance during bulk parsing
_AIRPORT_CACHE = {}

def get_airport_coordinates(iata_code):
    """
    Returns (lat, lon) or None if not found.
    Queries the database table 'Airport' and caches results in-memory.
    """
    if not iata_code:
        return None
    code = iata_code.strip().upper()
    
    if code in _AIRPORT_CACHE:
        return _AIRPORT_CACHE[code]
        
    try:
        airport = Airport.objects.get(iata_code=code)
        coords = (float(airport.latitude), float(airport.longitude))
        _AIRPORT_CACHE[code] = coords
        return coords
    except Airport.DoesNotExist:
        # Do not cache negative hits in case the airport is added to the DB later
        return None


def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates the Great Circle distance in km between two coordinate points."""
    # Earth radius in kilometers
    R = 6371.0
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    distance = R * c
    return distance

def get_flight_distance_km(origin_code, dest_code):
    """
    Calculates great circle flight distance in km with 9% routing uplift.
    Returns (distance_km, was_found).
    """
    coords1 = get_airport_coordinates(origin_code)
    coords2 = get_airport_coordinates(dest_code)
    
    if not coords1 or not coords2:
        return 0.0, False
        
    distance = calculate_haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1])
    # Apply 9% uplift routing adjustment (IPCC/DEFRA standard)
    adjusted_distance = distance * 1.09
    return adjusted_distance, True
