import unittest
from fit_modifier.modifier import format_seconds_to_hhmmss, parse_duration_to_seconds

class TestModifier(unittest.TestCase):
    def test_format_seconds(self):
        self.assertEqual(format_seconds_to_hhmmss(3600), "01:00:00")
        self.assertEqual(format_seconds_to_hhmmss(3661), "01:01:01")
        self.assertEqual(format_seconds_to_hhmmss(59), "00:00:59")

    def test_parse_duration(self):
        self.assertEqual(parse_duration_to_seconds("01:00:00"), 3600)
        self.assertEqual(parse_duration_to_seconds("10:00"), 600)
        self.assertEqual(parse_duration_to_seconds("45m"), 2700)
        self.assertEqual(parse_duration_to_seconds("1h"), 3600)
        self.assertEqual(parse_duration_to_seconds("120s"), 120)
        self.assertEqual(parse_duration_to_seconds("30"), 1800) # <=180 is assumed as minutes

if __name__ == "__main__":
    unittest.main()
