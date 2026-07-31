import unittest
import os
import tempfile
import datetime
from fit_modifier.creator import (
    parse_duration_to_seconds,
    format_seconds_to_hhmmss,
    generate_csv_content,
    batch_create_daily_workouts
)

class TestCreator(unittest.TestCase):
    def test_parse_duration(self):
        self.assertEqual(parse_duration_to_seconds("45"), 2700)
        self.assertEqual(parse_duration_to_seconds("00:45:00"), 2700)
        self.assertEqual(parse_duration_to_seconds("45m"), 2700)

    def test_format_seconds(self):
        self.assertEqual(format_seconds_to_hhmmss(3600), "01:00:00")
        self.assertEqual(format_seconds_to_hhmmss(2700), "00:45:00")

    def test_hiit_csv_content(self):
        start_dt = datetime.datetime(2026, 7, 31, 10, 0, 0)
        csv_out = generate_csv_content(start_dt, 300, 150, 250, "HIIT / Training")
        self.assertIn("heart_rate", csv_out)
        lines = csv_out.split("\n")
        record_lines = [l for l in lines if l.startswith("Data,4,record")]
        self.assertEqual(len(record_lines), 300)

    def test_batch_create_daily_workouts_headless(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            generated_files = batch_create_daily_workouts(
                output_dir=tmpdir,
                sport_mode="HIIT / Training",
                target_date_str=today_str,
                target_daily_calories=3000,
                calorie_tolerance=500,
                num_sessions=5,
                headless=True
            )
            self.assertEqual(len(generated_files), 5)
            for f in generated_files:
                self.assertTrue(os.path.exists(f))
                self.assertTrue(f.endswith(".fit"))

if __name__ == "__main__":
    unittest.main()
