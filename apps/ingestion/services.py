import os
from django.db import transaction
from apps.ingestion.models import DataSource, ActivityRecord
from apps.ingestion.parsers.registry import get_parser_for_source
from apps.emissions.calculator import calculate_record_emissions

def process_data_source_file(data_source_id):
    """
    Ingestion pipeline:
    1. Updates DataSource to 'processing'
    2. Instantiates appropriate parser via Registry factory
    3. Runs parsing, validating, normalizing
    4. Computes GHG emissions (Scope 1, 2, 3)
    5. Flags anomalous quantities or structural messiness
    6. Performs bulk database creation
    """
    try:
        data_source = DataSource.objects.get(id=data_source_id)
    except DataSource.DoesNotExist:
        return False
        
    data_source.status = 'processing'
    data_source.save()
    
    file_path = data_source.uploaded_file.path
    source_type = data_source.source_type
    
    try:
        parser = get_parser_for_source(source_type)
    except ValueError as err:
        data_source.status = 'failed'
        data_source.processing_log = str(err)
        data_source.save()
        return False
        
    try:
        # Step 1: Parse
        raw_rows = parser.parse(file_path)
        
        parsed_records = []
        error_count = 0
        logs = []
        
        # Step 2: Validate, Normalize & Calculate in Transaction
        with transaction.atomic():
            for row in raw_rows:
                row_num = row.get('_row_num', 0)
                is_valid, errors = parser.validate(row)
                
                if not is_valid:
                    error_count += 1
                    logs.append(f"Row {row_num} Validation Failed: {', '.join(errors)}")
                    continue
                    
                # Normalize schema
                normalized_data = parser.normalize(row)
                
                # Create instance (not saved yet)
                record = ActivityRecord(
                    data_source=data_source,
                    source_row_number=row_num,
                    activity_type=normalized_data['activity_type'],
                    description=normalized_data['description'],
                    activity_date=normalized_data['activity_date'],
                    period_start=normalized_data.get('period_start'),
                    period_end=normalized_data.get('period_end'),
                    facility_code=normalized_data.get('facility_code', ''),
                    facility_name=normalized_data.get('facility_name', ''),
                    quantity=normalized_data['quantity'],
                    unit=normalized_data['unit'],
                    original_quantity=normalized_data['original_quantity'],
                    original_unit=normalized_data['original_unit'],
                    scope=normalized_data['scope'],
                    raw_data=row,
                    source_metadata=normalized_data.get('source_metadata', {}),
                )
                
                # Step 3: Emissions calculation
                region = normalized_data.get('source_metadata', {}).get('region_grid', '')
                factor, emissions = calculate_record_emissions(
                    normalized_data['activity_type'].replace('fuel_combustion_', ''), 
                    normalized_data['quantity'], 
                    normalized_data['unit'],
                    region=region
                )
                record.emission_factor = factor
                record.co2e_kg = emissions
                
                # Step 4: Quality flags
                flag = parser.flag_suspicious(normalized_data)
                if flag:
                    record.status = 'flagged'
                    record.flag_reason = flag
                    logs.append(f"Row {row_num} Flagged: {flag}")
                    
                parsed_records.append(record)
                
            # Step 5: Bulk creation
            ActivityRecord.objects.bulk_create(parsed_records)
            
        # Complete
        data_source.status = 'completed'
        data_source.row_count = len(raw_rows)
        data_source.error_count = error_count
        data_source.processing_log = "\n".join(logs) if logs else "Imported successfully without errors."
        data_source.save()
        return True
        
    except Exception as exc:
        data_source.status = 'failed'
        data_source.processing_log = f"Critical Pipeline Exception: {str(exc)}"
        data_source.save()
        return False
