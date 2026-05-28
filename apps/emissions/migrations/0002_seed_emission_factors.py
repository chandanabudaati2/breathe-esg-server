from django.db import migrations
from datetime import date

def seed_factors(apps, schema_editor):
    EmissionFactor = apps.get_model('emissions', 'EmissionFactor')
    
    # Realistic 2025/2026 GHG coefficients (DEFRA / EPA grid mixes)
    factors = [
        # Scope 1 Combustions
        {
            'activity_type': 'diesel',
            'unit': 'l',
            'factor_kg_co2e': 2.6521,
            'source': 'DEFRA 2024',
            'region': 'DE',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'natural_gas',
            'unit': 'm3',
            'factor_kg_co2e': 1.9125,
            'source': 'DEFRA 2024',
            'region': 'DE',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'lpg',
            'unit': 'kg',
            'factor_kg_co2e': 2.9342,
            'source': 'DEFRA 2024',
            'region': 'DE',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'heating_oil',
            'unit': 'l',
            'factor_kg_co2e': 2.5401,
            'source': 'DEFRA 2024',
            'region': 'DE',
            'valid_from': date(2025, 1, 1),
        },
        
        # Scope 2 Electricity (Germany vs US Grid Mixes)
        {
            'activity_type': 'electricity_consumption',
            'unit': 'kwh',
            'factor_kg_co2e': 0.3820,
            'source': 'German UBA 2024',
            'region': 'de',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'electricity_consumption',
            'unit': 'kwh',
            'factor_kg_co2e': 0.2642,
            'source': 'US EPA eGRID 2023',
            'region': 'us',
            'valid_from': date(2025, 1, 1),
        },
        
        # Scope 3 Flights
        {
            'activity_type': 'flight_domestic',
            'unit': 'km',
            'factor_kg_co2e': 0.2451,
            'source': 'DEFRA 2024 (w/ RF)',
            'region': 'global',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'flight_short_haul',
            'unit': 'km',
            'factor_kg_co2e': 0.1512,
            'source': 'DEFRA 2024 (w/ RF)',
            'region': 'global',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'flight_long_haul',
            'unit': 'km',
            'factor_kg_co2e': 0.1203,
            'source': 'DEFRA 2024 (w/ RF)',
            'region': 'global',
            'valid_from': date(2025, 1, 1),
        },
        
        # Scope 3 Hotel stays (Country specific proxies)
        {
            'activity_type': 'hotel_stay_frankfurt',
            'unit': 'room_nights',
            'factor_kg_co2e': 82.4,
            'source': 'DEFRA 2024 Hotel Stays',
            'region': 'de',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'hotel_stay_london',
            'unit': 'room_nights',
            'factor_kg_co2e': 75.2,
            'source': 'DEFRA 2024 Hotel Stays',
            'region': 'gb',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'hotel_stay_boston',
            'unit': 'room_nights',
            'factor_kg_co2e': 62.1,
            'source': 'DEFRA 2024 Hotel Stays',
            'region': 'us',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'hotel_stay_new york',
            'unit': 'room_nights',
            'factor_kg_co2e': 68.4,
            'source': 'DEFRA 2024 Hotel Stays',
            'region': 'us',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'hotel_stay_munich',
            'unit': 'room_nights',
            'factor_kg_co2e': 82.4,
            'source': 'DEFRA 2024 Hotel Stays',
            'region': 'de',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'hotel_stay_shanghai',
            'unit': 'room_nights',
            'factor_kg_co2e': 95.8,
            'source': 'DEFRA 2024 Hotel Stays',
            'region': 'cn',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'hotel_stay_singapore',
            'unit': 'room_nights',
            'factor_kg_co2e': 78.3,
            'source': 'DEFRA 2024 Hotel Stays',
            'region': 'sg',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'hotel_stay_berlin',
            'unit': 'room_nights',
            'factor_kg_co2e': 82.4,
            'source': 'DEFRA 2024 Hotel Stays',
            'region': 'de',
            'valid_from': date(2025, 1, 1),
        },
        {
            'activity_type': 'hotel_stay_default',
            'unit': 'room_nights',
            'factor_kg_co2e': 70.0,
            'source': 'DEFRA 2024 Hotel Stays Proxy',
            'region': 'global',
            'valid_from': date(2025, 1, 1),
        },
        
        # Scope 3 Ground Transport Spend proxy (e.g. taxi / car rental)
        {
            'activity_type': 'ground_transport_other',
            'unit': 'eur',
            'factor_kg_co2e': 0.2104,
            'source': 'EEIO Spend Factors 2024',
            'region': 'de',
            'valid_from': date(2025, 1, 1),
        },
    ]
    
    for f in factors:
        EmissionFactor.objects.create(**f)

def rollback_factors(apps, schema_editor):
    EmissionFactor = apps.get_model('emissions', 'EmissionFactor')
    EmissionFactor.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_factors, rollback_factors),
    ]
