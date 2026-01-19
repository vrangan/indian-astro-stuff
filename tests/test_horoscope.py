import os
import unittest

# Ensure module import works regardless of cwd
import sys
sys.path.append('.')

from horoscope import generate_horoscope, SOUTH_INDIAN_STYLE, NORTH_INDIAN_STYLE


class TestHoroscopeGeneration(unittest.TestCase):
    def setUp(self):
        self.sample_event = {
            'Sun_Longitude': 285.0,
            'Moon_Longitude': 287.0,
            'Mars_Longitude': 120.0,
            'Mercury_Longitude': 290.0,
            'Jupiter_Longitude': 283.0,
            'Venus_Longitude': 282.0,
            'Saturn_Longitude': 200.0,
        }

    def test_south_indian_text_and_png(self):
        text, fname = generate_horoscope(self.sample_event, SOUTH_INDIAN_STYLE, 'test_horoscope_si.png', text_output=True)
        self.assertIsNotNone(text)
        self.assertIn('HOROSCOPE CHART - SOUTH_INDIAN', text)
        self.assertTrue(os.path.exists('test_horoscope_si.png'))

    def test_north_indian_text_and_png(self):
        text, fname = generate_horoscope(self.sample_event, NORTH_INDIAN_STYLE, 'test_horoscope_ni.png', text_output=True)
        self.assertIsNotNone(text)
        self.assertIn('HOROSCOPE CHART - NORTH_INDIAN', text)
        self.assertTrue(os.path.exists('test_horoscope_ni.png'))


if __name__ == '__main__':
    unittest.main()
