from django.contrib import admin
from .models import EmissionFactor, Airport

@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'unit', 'factor_kg_co2e', 'source', 'region', 'valid_from')
    list_filter = ('source', 'region', 'activity_type')
    search_fields = ('activity_type', 'source', 'region')

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('iata_code', 'name', 'latitude', 'longitude')
    search_fields = ('iata_code', 'name')
