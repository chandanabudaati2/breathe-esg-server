from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from apps.ingestion.models import ActivityRecord, DataSource

class DashboardStatsView(APIView):
    """
    Exposes high-level dashboard summaries:
    - Counts by review status
    - Breakdown by emissions scope
    - Carbon metric sums (total CO2e)
    - Activity record counts per ingestion source
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = ActivityRecord.objects.all()
        
        # Summarize by review status
        status_summary = records.values('status').annotate(count=Count('id'))
        status_dict = {
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'flagged': 0,
            'locked': 0,
        }
        for item in status_summary:
            status_dict[item['status']] = item['count']
            
        # Scope breakdown
        scope_summary = records.values('scope').annotate(
            count=Count('id'),
            co2e=Sum('co2e_kg')
        )
        scope_dict = {
            1: {'count': 0, 'co2e': 0.0},
            2: {'count': 0, 'co2e': 0.0},
            3: {'count': 0, 'co2e': 0.0},
        }
        for item in scope_summary:
            scope_dict[item['scope']] = {
                'count': item['count'],
                'co2e': float(item['co2e'] or 0.0)
            }
            
        # Ingestion metrics
        source_summary = records.values('data_source__source_type').annotate(
            count=Count('id'),
            co2e=Sum('co2e_kg')
        )
        source_dict = {}
        for item in source_summary:
            source_dict[item['data_source__source_type']] = {
                'count': item['count'],
                'co2e': float(item['co2e'] or 0.0)
            }
            
        # Overall carbon footprint sum
        total_co2e = records.aggregate(total=Sum('co2e_kg'))['total'] or 0.0
        
        return Response({
            'total_records': records.count(),
            'total_co2e_kg': float(total_co2e),
            'status': status_dict,
            'scopes': scope_dict,
            'sources': source_dict
        })
