from django.db import models

class EmissionFactor(models.Model):
    """Lookup table for green house gas emission factors (DEFRA, EPA, etc.)."""
    activity_type = models.CharField(max_length=100)  # e.g., 'diesel', 'natural_gas', 'electricity_de', 'flight_long', etc.
    unit = models.CharField(max_length=20)  # Unit of activity (e.g., L, kg, kWh, km)
    factor_kg_co2e = models.DecimalField(max_digits=12, decimal_places=6)
    source = models.CharField(max_length=100)  # e.g., 'DEFRA 2024', 'EPA eGRID 2023'
    region = models.CharField(max_length=50, blank=True)  # Grid or country code
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.activity_type} ({self.region}) - {self.factor_kg_co2e} kg CO2e/{self.unit}"


class Airport(models.Model):
    """Lookup table for airport locations and coordinates (Latitude/Longitude)."""
    iata_code = models.CharField(max_length=3, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"{self.iata_code} - {self.name or 'Unknown'} ({self.latitude}, {self.longitude})"

