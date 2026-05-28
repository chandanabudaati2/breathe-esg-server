from django.db import models
from django.contrib.auth.models import User

class DataSource(models.Model):
    """Tracks each uploaded raw data file and its processing status."""
    SOURCE_TYPES = [
        ('sap_fuel', 'SAP Fuel & Procurement'),
        ('utility', 'Utility Electricity'),
        ('travel', 'Corporate Travel'),
    ]
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    uploaded_file = models.FileField(upload_to='uploads/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='uploaded')
    row_count = models.IntegerField(null=True, blank=True)
    error_count = models.IntegerField(null=True, blank=True)
    processing_log = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_source_type_display()} - {self.name} ({self.status})"


class ActivityRecord(models.Model):
    """Normalized activity record. The unified model all source formats map into."""
    SCOPE_CHOICES = [
        (1, 'Scope 1 — Direct'),
        (2, 'Scope 2 — Indirect'),
        (3, 'Scope 3 — Other Indirect'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged — Suspicious'),
        ('locked', 'Locked for Audit'),
    ]

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='records')
    source_row_number = models.IntegerField()

    # Activity description
    activity_type = models.CharField(max_length=100)  # e.g., 'fuel_combustion', 'electricity', 'flight', 'hotel'
    description = models.TextField(blank=True)

    # Timeframe
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    # Site/Facility location
    facility_code = models.CharField(max_length=50, blank=True)
    facility_name = models.CharField(max_length=255, blank=True)

    # Normalized Quantities
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit = models.CharField(max_length=20)  # Liter, kg, kWh, km, room_nights
    original_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    original_unit = models.CharField(max_length=20)

    # Calculated Emissions
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    emission_factor = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=6)
    co2e_kg = models.DecimalField(null=True, blank=True, max_digits=15, decimal_places=4)

    # Preserving source metadata in standard JSONFields
    raw_data = models.JSONField(default=dict)
    source_metadata = models.JSONField(default=dict)

    # Workflow Review Lifecycle
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    flag_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.activity_type} - {self.quantity} {self.unit} ({self.status})"


class AuditLog(models.Model):
    """Tracks every mutation to an ActivityRecord for full audit trail."""
    ACTION_CHOICES = [
        ('status_change', 'Status Change'),
        ('edit', 'Field Edit'),
        ('lock', 'Audit Lock'),
        ('bulk_review', 'Bulk Review'),
    ]
    record = models.ForeignKey(ActivityRecord, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_changes')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"AuditLog: {self.record_id} {self.action} {self.field_name} by {self.changed_by}"
