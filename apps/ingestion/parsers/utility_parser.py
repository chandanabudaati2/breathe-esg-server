import csv
from datetime import datetime
from decimal import Decimal
from .base import BaseParser

# Flexible Header Maps for portals
UTILITY_HEADER_MAP = {
    'account number': 'account_number',
    'meter id': 'meter_id',
    'service address': 'service_address',
    'billing period start': 'period_start',
    'billing period end': 'period_end',
    'usage (kwh)': 'usage',
    'estimated/actual read': 'read_type',
    'total cost': 'cost',
    'currency': 'currency',
    'service point id': 'service_point_id',
}

class UtilityElectricityParser(BaseParser):
    """
    Parses utility provider electricity portal exports.
    Handles non-aligned billing cycles, kWh/MWh usage, and estimated reads.
    """
    
    def parse(self, file_path) -> list[dict]:
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = [h.strip().lower() for h in next(reader)]
            
            mapped_headers = [UTILITY_HEADER_MAP.get(h, h) for h in headers]
            
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
        if not row.get('meter_id'):
            errors.append("Missing Meter ID")
        if not row.get('period_start') or not row.get('period_end'):
            errors.append("Missing billing period dates")
        if not row.get('usage'):
            errors.append("Missing energy usage quantity")
            
        return len(errors) == 0, errors

    def normalize(self, row: dict) -> dict:
        raw_usage = row.get('usage', '0')
        raw_start = row.get('period_start', '')
        raw_end = row.get('period_end', '')
        meter_id = row.get('meter_id', '')
        address = row.get('service_address', '')
        
        # Parse start and end dates
        start_date = None
        end_date = None
        for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y'):
            try:
                if not start_date:
                    start_date = datetime.strptime(raw_start, fmt).date()
            except ValueError:
                pass
            try:
                if not end_date:
                    end_date = datetime.strptime(raw_end, fmt).date()
            except ValueError:
                pass
                
        # Fallbacks
        if not start_date:
            start_date = datetime.now().date()
        if not end_date:
            end_date = datetime.now().date()
            
        # Parse usage value
        try:
            usage_decimal = Decimal(raw_usage)
        except:
            usage_decimal = Decimal('0')
            
        # Standardize units.
        # If Meter ID contains "US", it reports in MWh. Standardize to kWh (x1000).
        normalized_qty = usage_decimal
        original_unit = 'kWh'
        normalized_unit = 'kwh'
        
        if 'US' in meter_id:
            original_unit = 'MWh'
            normalized_qty = usage_decimal * Decimal('1000')
            
        # Extract region grid
        region = 'de'
        if 'US' in meter_id:
            region = 'us'
            
        return {
            'activity_type': 'electricity_consumption',
            'description': f"Electricity Meter {meter_id} - Service Location: {address}",
            'activity_date': end_date,
            'period_start': start_date,
            'period_end': end_date,
            'facility_code': meter_id,
            'facility_name': address,
            'quantity': normalized_qty,
            'unit': normalized_unit,
            'original_quantity': usage_decimal,
            'original_unit': original_unit,
            'scope': 2,
            'source_metadata': {
                'account_number': row.get('account_number', ''),
                'read_type': row.get('read_type', 'Actual'),
                'cost': row.get('cost', '0'),
                'service_point_id': row.get('service_point_id', ''),
                'region_grid': region,
            }
        }

    def flag_suspicious(self, record_data: dict) -> str | None:
        start = record_data.get('period_start')
        end = record_data.get('period_end')
        metadata = record_data.get('source_metadata', {})
        read_type = metadata.get('read_type', '').lower()
        
        if read_type == 'estimated':
            return "Usage reported using an Estimated meter reading"
            
        if start and end:
            days = (end - start).days
            if days > 45:
                return f"Abnormally long billing period: {days} days (> 45 days)"
            if days < 20:
                return f"Abnormally short billing period: {days} days (< 20 days)"
                
        return None
