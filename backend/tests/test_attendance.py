"""Attendance computation tests."""

import unittest

from app.domain.attendance import AttendanceError, normalize_status, summarize


class TestNormalize(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(normalize_status("Present"), "present")
        self.assertEqual(normalize_status(" LATE "), "late")

    def test_invalid(self):
        with self.assertRaises(AttendanceError):
            normalize_status("teleported")


class TestSummarize(unittest.TestCase):
    def test_counts_and_rate(self):
        s = summarize(["present", "absent", "late", "present", "excused"])
        self.assertEqual(s.total, 5)
        self.assertEqual(s.present, 2)
        self.assertEqual(s.absent, 1)
        self.assertEqual(s.late, 1)
        self.assertEqual(s.excused, 1)
        # attended = present+late+excused = 4 of 5
        self.assertEqual(s.rate, 0.8)

    def test_empty(self):
        s = summarize([])
        self.assertEqual(s.total, 0)
        self.assertEqual(s.rate, 0.0)

    def test_all_absent(self):
        s = summarize(["absent", "absent"])
        self.assertEqual(s.rate, 0.0)


if __name__ == "__main__":
    unittest.main()
