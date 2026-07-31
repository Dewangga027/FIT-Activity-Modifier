import unittest
from fit_modifier.modifier import (
    format_seconds_to_hhmmss,
    parse_duration_to_seconds,
    calculate_hr_zones,
    calculate_trimp,
    humanize_hr_series
)

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

    def test_calculate_hr_zones(self):
        hrs = [100, 120, 140, 160, 180]
        zones = calculate_hr_zones(hrs, max_hr=190)
        self.assertIn("Z1", zones)
        self.assertIn("Z5", zones)
        total_pct = sum([z["pct"] for z in zones.values()])
        self.assertAlmostEqual(total_pct, 100.0, delta=1.0)

    def test_calculate_trimp(self):
        hrs = [140] * 600 # 10 minutes at 140 bpm
        trimp = calculate_trimp(hrs, sample_interval_sec=1, max_hr=190, rest_hr=60)
        self.assertGreater(trimp, 0.0)

    def test_humanize_hr_series(self):
        orig_hrs = [130] * 100
        target_avg = 150
        humanized = humanize_hr_series(orig_hrs, target_avg_hr=target_avg)
        self.assertEqual(len(humanized), len(orig_hrs))
        # Verify exact average target precision
        calc_avg = int(round(sum(humanized) / len(humanized)))
        self.assertEqual(calc_avg, target_avg)
        # Verify clamping boundaries
        for hr in humanized:
            self.assertGreaterEqual(hr, 40)
            self.assertLessEqual(hr, 220)

if __name__ == "__main__":
    unittest.main()

