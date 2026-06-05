"""Grading / report-card computation tests."""

import unittest

from app.domain.grading import (
    GradingError,
    SubjectResult,
    compute_report_card,
    grade_for_score,
    grade_point_for_score,
    rank_students,
)


class TestGradeBands(unittest.TestCase):
    def test_grade_boundaries(self):
        self.assertEqual(grade_for_score(80), "A")
        self.assertEqual(grade_for_score(79.99), "B")
        self.assertEqual(grade_for_score(50), "D")
        self.assertEqual(grade_for_score(49), "F")

    def test_grade_points(self):
        self.assertEqual(grade_point_for_score(85), 4.0)
        self.assertEqual(grade_point_for_score(0), 0.0)

    def test_out_of_range(self):
        with self.assertRaises(GradingError):
            grade_for_score(101)
        with self.assertRaises(GradingError):
            grade_for_score(-1)


class TestReportCard(unittest.TestCase):
    def test_aggregation(self):
        rc = compute_report_card(
            "stu1",
            [SubjectResult("Math", 90), SubjectResult("English", 60)],
        )
        self.assertEqual(rc.total, 150.0)
        self.assertEqual(rc.average, 75.0)
        self.assertEqual(rc.overall_grade, "B")
        self.assertEqual(rc.gpa, 3.0)  # (4.0 + 2.0) / 2

    def test_empty_rejected(self):
        with self.assertRaises(GradingError):
            compute_report_card("stu1", [])


class TestRanking(unittest.TestCase):
    def test_competition_ranking_with_ties(self):
        ranking = rank_students({"a": 90, "b": 90, "c": 70})
        self.assertEqual(ranking, [("a", 1), ("b", 1), ("c", 3)])

    def test_simple_order(self):
        ranking = rank_students({"x": 50, "y": 80})
        self.assertEqual(ranking, [("y", 1), ("x", 2)])


if __name__ == "__main__":
    unittest.main()
