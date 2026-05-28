from decimal import Decimal
from .models import EmissionFactor

def calculate_record_emissions(activity_type, quantity, unit, region=''):
    """
    Looks up appropriate emission factors and returns (factor, emissions_kg).
    If no factor matches, returns (None, None).
    """
    if quantity is None:
        return None, None
        
    # Attempt to query from database
    queryset = EmissionFactor.objects.filter(
        activity_type=activity_type,
        unit=unit
    )
    
    if region:
        # Match regional factors if possible (e.g. electrical grids)
        regional_match = queryset.filter(region=region).first()
        if regional_match:
            factor = regional_match.factor_kg_co2e
            return factor, Decimal(quantity) * factor
            
    # Default matching
    match = queryset.first()
    if match:
        factor = match.factor_kg_co2e
        return factor, Decimal(quantity) * factor
        
    return None, None
