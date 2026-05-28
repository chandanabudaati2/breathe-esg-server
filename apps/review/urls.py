from django.urls import path
from apps.review.views import DashboardStatsView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
