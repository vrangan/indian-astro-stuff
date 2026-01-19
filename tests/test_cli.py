import sys
import unittest

# Ensure module import works regardless of cwd
sys.path.append('.')

from ThiruppavaiDating import parse_arguments, LOCATIONS


class TestCLIParseArguments(unittest.TestCase):
    def test_parse_arguments_with_vj_alignment(self):
        argv = [
            'prog',
            '--year-range', '-6000', '-5990',
            '--location', 'Chennai',
            '--tithi', '14',
            '--vj-only',
            '--vj-tolerance', '5.0',
            '--vj-altitude', '0.0',
            '--quiet'
        ]
        old_argv = sys.argv
        try:
            sys.argv = argv
            args, config, settings, lat, lon, name = parse_arguments()
            self.assertEqual(tuple(settings['year_range']), (-6000, -5990))
            self.assertEqual(lat, LOCATIONS['Chennai']['lat'])
            self.assertEqual(lon, LOCATIONS['Chennai']['lon'])
            self.assertTrue(config.require_vj_alignment)
            self.assertEqual(config.vj_tolerance_degrees, 5.0)
            self.assertEqual(config.vj_altitude_above_horizon, 0.0)
            self.assertEqual(config.target_tithi, 14)
        finally:
            sys.argv = old_argv

    def test_parse_arguments_disable_vj_alignment(self):
        argv = [
            'prog',
            '--year-range', '-6000', '-5990',
            '--location', 'Ujjain',
            '--no-vj',
            '--quiet'
        ]
        old_argv = sys.argv
        try:
            sys.argv = argv
            args, config, settings, lat, lon, name = parse_arguments()
            self.assertFalse(config.require_vj_alignment)
            self.assertEqual(tuple(settings['year_range']), (-6000, -5990))
            self.assertEqual(name, LOCATIONS['Ujjain']['name'])
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
