from rest_framework import serializers
from apps.ingestion.models import DataSource, ActivityRecord

class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'source_type', 'uploaded_file', 
            'uploaded_by', 'uploaded_at', 'status', 
            'row_count', 'error_count', 'processing_log'
        ]
        read_only_fields = ['status', 'row_count', 'error_count', 'processing_log', 'uploaded_by']


class ActivityRecordSerializer(serializers.ModelSerializer):
    source_type_display = serializers.CharField(source='data_source.get_source_type_display', read_only=True)
    source_type = serializers.CharField(source='data_source.source_type', read_only=True)
    source_file_name = serializers.CharField(source='data_source.name', read_only=True)
    
    class Meta:
        model = ActivityRecord
        fields = [
            'id', 'data_source', 'source_type', 'source_type_display', 
            'source_file_name', 'source_row_number', 'activity_type', 
            'description', 'activity_date', 'period_start', 'period_end',
            'facility_code', 'facility_name', 'quantity', 'unit',
            'original_quantity', 'original_unit', 'scope', 'emission_factor',
            'co2e_kg', 'raw_data', 'source_metadata', 'status', 
            'flag_reason', 'reviewed_by', 'reviewed_at', 'review_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'data_source', 'source_row_number', 'activity_type', 
            'description', 'activity_date', 'period_start', 'period_end',
            'facility_code', 'facility_name', 'quantity', 'unit',
            'original_quantity', 'original_unit', 'scope', 'emission_factor',
            'co2e_kg', 'raw_data', 'source_metadata', 'created_at', 'updated_at'
        ]
