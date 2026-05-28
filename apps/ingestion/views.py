from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.ingestion.models import DataSource, ActivityRecord, AuditLog
from apps.ingestion.serializers import DataSourceSerializer, ActivityRecordSerializer
from apps.ingestion.services import process_data_source_file

class DataSourceViewSet(viewsets.ModelViewSet):
    """
    Handles DataSource uploading and background orchestration logs.
    """
    queryset = DataSource.objects.all().order_by('-uploaded_at')
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Bind user and save model
        data_source = serializer.save(uploaded_by=self.request.user)
        # Synchronously run prototype parsing pipeline
        process_data_source_file(data_source.id)
        # Refresh the instance from DB so the serialized response has the latest status
        data_source.refresh_from_db()


class ActivityRecordViewSet(viewsets.ModelViewSet):
    """
    Handles review, search, and audit locks for unified activity rows.
    """
    queryset = ActivityRecord.objects.all().order_by('id')
    serializer_class = ActivityRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        
        # Ingestion Source filtering
        source_type = self.request.query_params.get('source_type')
        if source_type:
            qs = qs.filter(data_source__source_type=source_type)
            
        # Status filtering
        review_status = self.request.query_params.get('status')
        if review_status:
            qs = qs.filter(status=review_status)
            
        # Scope filtering
        scope = self.request.query_params.get('scope')
        if scope:
            qs = qs.filter(scope=scope)
            
        # Date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            qs = qs.filter(activity_date__gte=start_date)
        if end_date:
            qs = qs.filter(activity_date__lte=end_date)
            
        # Search description
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(description__icontains=search)
            
        return qs

    @action(detail=True, methods=['patch'], url_path='review')
    def review_record(self, request, pk=None):
        """
        Analyst decision endpoint to approve, reject, or flag a single row.
        Creates an AuditLog entry for every status change.
        """
        record = self.get_object()
        if record.status == 'locked':
            return Response(
                {"error": "This record is locked for audit and cannot be modified."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        new_status = request.data.get('status')
        notes = request.data.get('review_notes', '')
        
        if new_status not in ['approved', 'rejected', 'flagged', 'pending']:
            return Response(
                {"error": "Invalid review status decision"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = record.status
        record.status = new_status
        record.review_notes = notes
        record.reviewed_by = request.user
        record.reviewed_at = datetime.now()
        record.save()
        
        # Audit trail entry
        AuditLog.objects.create(
            record=record,
            action='status_change',
            field_name='status',
            old_value=old_status,
            new_value=new_status,
            changed_by=request.user
        )
        
        return Response(self.get_serializer(record).data)

    @action(detail=False, methods=['post'], url_path='bulk-review')
    def bulk_review(self, request):
        """
        Allows analysts to perform actions across multiple records simultaneously.
        Creates AuditLog entries for each affected record.
        """
        record_ids = request.data.get('ids', [])
        new_status = request.data.get('status')
        notes = request.data.get('review_notes', '')
        
        if new_status not in ['approved', 'rejected', 'flagged', 'pending']:
            return Response(
                {"error": "Invalid review status decision"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        records = ActivityRecord.objects.filter(id__in=record_ids)
        locked_records = records.filter(status='locked')
        if locked_records.exists():
            return Response(
                {"error": "Some selected records are locked for audit and cannot be modified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log each individual change before bulk update
        audit_logs = []
        for record in records:
            audit_logs.append(AuditLog(
                record=record,
                action='bulk_review',
                field_name='status',
                old_value=record.status,
                new_value=new_status,
                changed_by=request.user
            ))
        AuditLog.objects.bulk_create(audit_logs)
            
        updated_count = records.update(
            status=new_status,
            review_notes=notes,
            reviewed_by=request.user,
            reviewed_at=datetime.now()
        )
        
        return Response({"message": f"Successfully updated {updated_count} records to {new_status}."})

    @action(detail=False, methods=['post'], url_path='lock')
    def lock_approved_records(self, request):
        """
        Irreversible locking workflow that seals approved records for auditors.
        Creates AuditLog entries for each locked record.
        """
        approved_records = ActivityRecord.objects.filter(status='approved')
        
        # Log each lock event
        audit_logs = []
        for record in approved_records:
            audit_logs.append(AuditLog(
                record=record,
                action='lock',
                field_name='status',
                old_value='approved',
                new_value='locked',
                changed_by=request.user
            ))
        AuditLog.objects.bulk_create(audit_logs)
        
        count = approved_records.update(status='locked')
        return Response({"message": f"Successfully locked {count} approved records for audit."})
