import csv
import re
from datetime import datetime
from decimal import Decimal
from .base import BaseParser

# Mapping German/English headers to key properties
SAP_HEADER_MAP = {
    'bestellnummer': 'po_number',
    'buchungskreis': 'company_code',
    'belegdatum': 'document_date',
    'lieferant': 'vendor_id',
    'lieferantenname': 'vendor_name',
    'position': 'item_number',
    'materialnummer': 'material_number',
    'kurztext': 'description',
    'bestellmenge': 'quantity',
    'mengeneinheit': 'unit',
    'nettopreis': 'price',
    'waehrung': 'currency',
    'werk': 'plant_code',
    'lagerort': 'storage_location',
}

# Material ID to Activity Classification
SAP_MATERIAL_TYPES = {
    '000000000050000101': 'diesel',
    '000000000050000103': 'natural_gas',
    '000000000050000104': 'lpg',
    '000000000050000105': 'heating_oil',
}

# Plant Code to Names/Locations
SAP_PLANTS = {
    '1000': ('Stuttgart Hauptwerk', 'DE'),
    '2100': ('Hamburg Process Facility', 'DE'),
    '3500': ('Munich Logistical Hub', 'DE'),
}

class SAPProcurementParser(BaseParser):
    """
    Parses typical SAP MM procurement flat files.
    Supports semicolon delimiters, German locale, DD.MM.YYYY dates, and unit conversions.
    """
    
    def parse(self, file_path) -> list[dict]:
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            # Semicolon is standard for DACH region SAP exports
            reader = csv.reader(f, delimiter=';')
            headers = [h.strip().lower() for h in next(reader)]
            
            # Map raw headers
            mapped_headers = [SAP_HEADER_MAP.get(h, h) for h in headers]
            
            for line_idx, row in enumerate(reader, start=2):
                if not row or not any(row):
                    continue
                record = {'_row_num': line_idx}
                for idx, val in enumerate(row):
                    if idx < len(mapped_headers):
                        record[mapped_headers[idx]] = val.strip()
                records.append(record)
        return records

    def validate(self, row: dict) -> tuple[bool, list[str]]:
        errors = []
        # Mandatories
        if not row.get('po_number'):
            errors.append("Missing Purchase Order number (Bestellnummer)")
        if not row.get('document_date'):
            errors.append("Missing Document Date (Belegdatum)")
        if not row.get('quantity'):
            errors.append("Missing Order Quantity (Bestellmenge)")
            
        return len(errors) == 0, errors

    def normalize(self, row: dict) -> dict:
        raw_qty = row.get('quantity', '0')
        raw_unit = row.get('unit', '').upper()
        raw_date = row.get('document_date', '')
        mat_num = row.get('material_number', '')
        plant = row.get('plant_code', '')
        
        # Parse Dates (German DD.MM.YYYY or ISO format)
        activity_date = None
        for fmt in ('%d.%m.%y', '%d.%m.%Y', '%Y-%m-%d'):
            try:
                activity_date = datetime.strptime(raw_date, fmt).date()
                break
            except ValueError:
                continue
        if not activity_date:
            activity_date = datetime.now().date()
            
        # Parse Quantities
        try:
            qty_decimal = Decimal(raw_qty.replace(',', '.'))
        except:
            qty_decimal = Decimal('0')
            
        # Classify fuel combustion activity
        activity_type = SAP_MATERIAL_TYPES.get(mat_num, 'unknown_fuel')
        
        # Unit Conversions
        normalized_qty = qty_decimal
        normalized_unit = raw_unit
        
        if raw_unit == 'GAL':  # Convert US Gallons to Liters
            normalized_qty = qty_decimal * Decimal('3.78541')
            normalized_unit = 'L'
        elif raw_unit == 'M3' and activity_type == 'natural_gas':
            normalized_qty = qty_decimal
            normalized_unit = 'm3'
        elif raw_unit == 'KG':
            normalized_qty = qty_decimal
            normalized_unit = 'kg'
        elif raw_unit == 'ST': # Standard German unit code for Pieces (Stück)
            normalized_qty = qty_decimal
            normalized_unit = 'pcs'
            
        # Plant Code lookup
        facility_name, region = SAP_PLANTS.get(plant, ('Unknown Plant', 'DE'))
        
        return {
            'activity_type': f"fuel_combustion_{activity_type}" if activity_type != 'unknown_fuel' else 'unknown_procurement',
            'description': f"SAP Procurement: {row.get('description', 'Fuel Purchase')}",
            'activity_date': activity_date,
            'facility_code': plant,
            'facility_name': facility_name,
            'quantity': normalized_qty,
            'unit': normalized_unit.lower(),
            'original_quantity': qty_decimal,
            'original_unit': raw_unit,
            'scope': 1 if activity_type != 'unknown_fuel' else 3,
            'source_metadata': {
                'vendor_id': row.get('vendor_id', ''),
                'vendor_name': row.get('vendor_name', ''),
                'po_number': row.get('po_number', ''),
                'material_number': mat_num,
            }
        }

    def flag_suspicious(self, record_data: dict) -> str | None:
        qty = record_data.get('quantity', Decimal('0'))
        original_qty = record_data.get('original_quantity', Decimal('0'))
        unit = record_data.get('unit', '')
        
        # Flag rules
        if qty <= 0:
            return "Zero or negative procurement quantity"
            
        if record_data.get('activity_type') == 'unknown_procurement':
            return "Unknown SAP material master number (failed lookup)"
            
        # Outlier bounds check (e.g. abnormally large diesel delivery)
        if record_data.get('activity_type') == 'fuel_combustion_diesel' and qty > 10000:
            return "Abnormally large volume diesel procurement (> 10,000 Liters)"
            
        # Check for future dates
        if record_data.get('activity_date') > datetime.now().date():
            return "Transaction date is set in the future"
            
        return None
