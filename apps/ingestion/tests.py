import os
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from apps.ingestion.models import DataSource, ActivityRecord
from apps.ingestion.parsers.sap_parser import SAPProcurementParser
from apps.ingestion.parsers.utility_parser import UtilityElectricityParser
from apps.ingestion.parsers.travel_parser import ConcurTravelParser

class ParserVerificationTests(TestCase):
    
    def test_sap_parser_normalization(self):
        parser = SAPProcurementParser()
        
        # Post-parsed row with mapped lowercase keys
        mapped_row = {
            'po_number': '4500001001',
            'document_date': '15.01.2025',
            'material_number': '000000000050000101', # Diesel
            'quantity': '100.5',
            'unit': 'L',
            'plant_code': '1000',
            'description': 'Diesel B7'
        }
        
        # Test validation
        is_ok, errors = parser.validate(mapped_row)
        self.assertTrue(is_ok)
        
        # Test normalization
        norm = parser.normalize(mapped_row)
        self.assertEqual(norm['activity_type'], 'fuel_combustion_diesel')
        self.assertEqual(norm['quantity'], Decimal('100.5'))
        self.assertEqual(norm['unit'], 'l')
        self.assertEqual(norm['facility_name'], 'Stuttgart Hauptwerk')
        
    def test_sap_parser_unit_conversion(self):
        parser = SAPProcurementParser()
        mapped_row_gal = {
            'po_number': '4500001009',
            'document_date': '15.03.2025',
            'material_number': '000000000050000101', # Diesel
            'quantity': '10',
            'unit': 'GAL',
            'plant_code': '1000'
        }
        norm = parser.normalize(mapped_row_gal)
        # 10 GAL * 3.78541 = 37.8541 L
        self.assertAlmostEqual(float(norm['quantity']), 37.8541, places=3)
        self.assertEqual(norm['unit'], 'l')

    def test_utility_parser_mwh_conversion(self):
        parser = UtilityElectricityParser()
        mapped_row = {
            'meter_id': 'MTR-US-01', # Contains 'US' so it triggers MWh conversion
            'period_start': '01.01.2025',
            'period_end': '31.01.2025',
            'usage': '4.5',
            'service_address': 'Boston premise'
        }
        
        is_ok, errors = parser.validate(mapped_row)
        self.assertTrue(is_ok)
        
        norm = parser.normalize(mapped_row)
        # 4.5 MWh * 1000 = 4500 kWh
        self.assertEqual(norm['quantity'], Decimal('4500'))
        self.assertEqual(norm['unit'], 'kwh')
        
    def test_travel_parser_flight_haversine(self):
        parser = ConcurTravelParser()
        mapped_flight_row = {
            'expense_type': 'Airfare',
            'transaction_date': '10.01.2025',
            'amount': '450.00',
            'description': 'Flight from STR to FRA',
            'city': 'Frankfurt'
        }
        
        is_ok, errors = parser.validate(mapped_flight_row)
        self.assertTrue(is_ok)
        
        norm = parser.normalize(mapped_flight_row)
        self.assertEqual(norm['unit'], 'km')
        self.assertGreater(float(norm['quantity']), 0)
        self.assertEqual(norm['activity_type'], 'flight_domestic') # STR to FRA is short (<483km)
        
    def test_travel_parser_hotel_nights(self):
        parser = ConcurTravelParser()
        mapped_hotel_row = {
            'expense_type': 'Hotel',
            'transaction_date': '10.01.2025',
            'amount': '360.00',
            'description': '2 nights hotel stay',
            'city': 'Frankfurt'
        }
        
        norm = parser.normalize(mapped_hotel_row)
        self.assertEqual(norm['quantity'], Decimal('2'))
        self.assertEqual(norm['unit'], 'room_nights')
        self.assertEqual(norm['activity_type'], 'hotel_stay_frankfurt')
