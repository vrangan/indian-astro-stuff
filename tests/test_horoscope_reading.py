"""Tests for basic horoscope reading functionality."""

import sys
import unittest
from datetime import datetime

# Ensure module import works regardless of cwd
sys.path.append('.')

from horoscope import basic_horoscope_reading


class TestHoroscopeReading(unittest.TestCase):
    """Test basic horoscope reading generation."""

    def test_reading_from_string_datetime(self):
        """Test reading with ISO datetime string."""
        reading, data = basic_horoscope_reading(
            birth_dt="1990-01-01T12:34:00",
            latitude=13.0827,
            longitude=80.2707,
            timezone="Asia/Kolkata",
        )
        
        # Check that reading is non-empty
        self.assertIsInstance(reading, str)
        self.assertGreater(len(reading), 100)
        self.assertIn("Introductory Horoscope Reading", reading)
        
        # Check all planets are present
        self.assertIn("Sun:", reading)
        self.assertIn("Moon:", reading)
        self.assertIn("Mars:", reading)
        self.assertIn("Mercury:", reading)
        self.assertIn("Jupiter:", reading)
        self.assertIn("Venus:", reading)
        self.assertIn("Saturn:", reading)
        self.assertIn("Rahu:", reading)
        self.assertIn("Ketu:", reading)
        
        # Check data dictionary
        self.assertIn('sun_lon_sid', data)
        self.assertIn('moon_lon_sid', data)
        self.assertIn('mars_lon_sid', data)
        self.assertIn('mercury_lon_sid', data)
        self.assertIn('jupiter_lon_sid', data)
        self.assertIn('venus_lon_sid', data)
        self.assertIn('saturn_lon_sid', data)
        self.assertIn('rahu_lon_sid', data)
        self.assertIn('ketu_lon_sid', data)
        self.assertIn('moon_nakshatra', data)
        self.assertIn('rahu_nakshatra', data)
        self.assertIn('ketu_nakshatra', data)

    def test_reading_with_datetime_object(self):
        """Test reading with datetime object."""
        dt = datetime(1990, 1, 1, 12, 34, 0)
        reading, data = basic_horoscope_reading(
            birth_dt=dt,
            latitude=13.0827,
            longitude=80.2707,
            timezone="Asia/Kolkata",
        )
        
        self.assertIsInstance(reading, str)
        self.assertIn("Introductory Horoscope Reading", reading)

    def test_reading_with_chart_generation(self):
        """Test reading with chart generation enabled."""
        reading, data = basic_horoscope_reading(
            birth_dt="1990-01-01T12:34:00",
            latitude=13.0827,
            longitude=80.2707,
            timezone="Asia/Kolkata",
            generate_chart=True,
            chart_style='south_indian',
        )
        
        self.assertIn('chart_file', data)
        self.assertTrue(data['chart_file'].endswith('.png'))
        
    def test_all_planet_longitudes_valid(self):
        """Test that all planet longitudes are in valid range [0, 360)."""
        reading, data = basic_horoscope_reading(
            birth_dt="2000-06-15T18:30:00",
            latitude=23.1765,  # Ujjain
            longitude=75.0,
            timezone="Asia/Kolkata",
        )
        
        for key in ['sun_lon_sid', 'moon_lon_sid', 'mars_lon_sid', 'mercury_lon_sid',
                    'jupiter_lon_sid', 'venus_lon_sid', 'saturn_lon_sid', 
                    'rahu_lon_sid', 'ketu_lon_sid']:
            self.assertIn(key, data)
            self.assertGreaterEqual(data[key], 0.0)
            self.assertLess(data[key], 360.0)


if __name__ == '__main__':
    unittest.main()
