from .sap_parser import SAPProcurementParser
from .utility_parser import UtilityElectricityParser
from .travel_parser import ConcurTravelParser

# Extensible registry linking keys to parser strategies
PARSER_REGISTRY = {
    'sap_fuel': SAPProcurementParser,
    'utility': UtilityElectricityParser,
    'travel': ConcurTravelParser,
}

def get_parser_for_source(source_type):
    """
    Registry pattern factory. Returns an initialized parser strategy
    supporting robust extensibility.
    """
    parser_class = PARSER_REGISTRY.get(source_type)
    if not parser_class:
        raise ValueError(f"No parser registered for source type: {source_type}")
    return parser_class()
