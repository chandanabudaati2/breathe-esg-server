import csv
import re
from datetime import datetime
from decimal import Decimal
from apps.ingestion.parsers.base import BaseParser
from apps.emissions.airport_data import get_flight_distance_km

# Tabular Concur headers mapping
TRAVEL_HEADER_MAP = {
    'report name': 'report_name',
    'employee name': 'employee_name',
    'employee id': 'employee_id',
    'transaction date': 'transaction_date',
    'expense type': 'expense_type',
    'vendor': 'vendor',
    'city': 'city',
    'business purpose': 'purpose',
    'amount': 'amount',
    'currency': 'currency',
    'payment type': 'payment_type',
    'approval status': 'status',
    'cost center': 'cost_center',
    'description': 'description',
}

class ConcurTravelParser(BaseParser):
    """
    Parses Concur standard tabular accounting formats.
    Extracts IATA codes, computes Haversine flight distance with 9% routing uplift.
    """
    
    def parse(self, file_path) -> list[dict]:
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = [h.strip().lower() for h in next(reader)]
            
            mapped_headers = [TRAVEL_HEADER_MAP.get(h, h) for h in headers]
            
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
        if not row.get('expense_type'):
            errors.append("Missing Expense Type")
        if not row.get('transaction_date'):
            errors.append("Missing Transaction Date")
        if not row.get('amount'):
            errors.append("Missing transaction amount")
            
        return len(errors) == 0, errors

    def normalize(self, row: dict) -> dict:
        exp_type = row.get('expense_type', '').lower()
        raw_date = row.get('transaction_date', '')
        raw_amt = row.get('amount', '0')
        currency = row.get('currency', 'EUR')
        desc = row.get('description', '')
        city = row.get('city', '')
        
        # Parse transaction date
        activity_date = None
        for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y'):
            try:
                activity_date = datetime.strptime(raw_date, fmt).date()
                break
            except ValueError:
                continue
        if not activity_date:
            activity_date = datetime.now().date()
            
        # Parse transaction amount
        try:
            amount_decimal = Decimal(raw_amt)
        except:
            amount_decimal = Decimal('0')
            
        # Normalization properties
        activity_type = 'travel_other'
        description_norm = f"Travel Expense: {row.get('vendor', 'Unknown')} - {desc}"
        quantity = Decimal('0')
        unit = 'spend'
        
        source_metadata = {
            'employee_name': row.get('employee_name', ''),
            'employee_id': row.get('employee_id', ''),
            'report_name': row.get('report_name', ''),
            'cost_center': row.get('cost_center', ''),
            'vendor': row.get('vendor', ''),
            'original_currency': currency,
            'original_amount': float(amount_decimal),
        }

        # Sub-category processing
        if 'air' in exp_type or 'flight' in exp_type:
            # Parse flight segment IATA codes e.g. "Flight from FRA to LHR"
            match = re.search(r'([A-Z]{3})\s*(?:to|to/from|-)\s*([A-Z]{3})', desc.upper(), re.IGNORECASE)
            origin, dest = '', ''
            
            if match:
                origin, dest = match.group(1), match.group(2)
                distance, found = get_flight_distance_km(origin, dest)
                if found:
                    quantity = Decimal(str(round(distance, 2)))
                    unit = 'km'
                    # Haul classifications
                    if distance < 483:
                        activity_type = 'flight_domestic'
                    elif distance < 3700:
                        activity_type = 'flight_short_haul'
                    else:
                        activity_type = 'flight_long_haul'
                else:
                    activity_type = 'flight_unresolved'
            else:
                activity_type = 'flight_unresolved'
                
            source_metadata['flight_origin'] = origin
            source_metadata['flight_destination'] = dest
            
        elif 'hotel' in exp_type or 'lodging' in exp_type:
            # Extract number of room nights from description
            nights_match = re.search(r'(\d+)\s*night', desc.lower())
            nights = 1
            if nights_match:
                nights = int(nights_match.group(1))
            quantity = Decimal(nights)
            unit = 'room_nights'
            activity_type = f"hotel_stay_{city.lower()}" if city else 'hotel_stay_default'
            
        elif 'taxi' in exp_type or 'car' in exp_type or 'mileage' in exp_type:
            activity_type = 'ground_transport_other'
            quantity = amount_decimal
            unit = 'eur'  # Spend-based proxy
            
        return {
            'activity_type': activity_type,
            'description': description_norm,
            'activity_date': activity_date,
            'facility_code': row.get('cost_center', 'CC-GLOBAL'),
            'facility_name': f"Cost Center {row.get('cost_center', 'CC-GLOBAL')}",
            'quantity': quantity,
            'unit': unit,
            'original_quantity': quantity if quantity > 0 else amount_decimal,
            'original_unit': unit if quantity > 0 else currency.lower(),
            'scope': 3,
            'source_metadata': source_metadata,
        }

    def flag_suspicious(self, record_data: dict) -> str | None:
        activity_type = record_data.get('activity_type', '')
        metadata = record_data.get('source_metadata', {})
        amount = metadata.get('original_amount', Decimal('0'))
        
        # Flight exceptions
        if 'flight' in activity_type:
            if activity_type == 'flight_unresolved':
                return "Failed to parse airport origin/destination codes from flight expense"
            if amount > 5000:
                return f"Abnormally high travel transaction amount: {amount} EUR/USD"
                
        # Hotel stays lacking geographic location
        if 'hotel' in activity_type and activity_type == 'hotel_stay_default':
            return "Hotel stay expense lacks city indicator for geographic emission mapping"
            
        return None
