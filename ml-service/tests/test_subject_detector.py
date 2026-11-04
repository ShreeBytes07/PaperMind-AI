import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from subject_detector import detect_subject


class SubjectDetectorTests(unittest.TestCase):

    def test_java_question_is_accepted(self):
        result = detect_subject("Explain inheritance in Java.")
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["subject"], "Java")

    def test_python_question_is_skipped(self):
        result = detect_subject("Explain Python decorators.")
        self.assertEqual(result["status"], "skipped")

    def test_sql_question_is_skipped(self):
        result = detect_subject("Write an SQL query to select students.")
        self.assertEqual(result["status"], "skipped")

    def test_c_question_is_skipped(self):
        result = detect_subject("Write a C program using printf.")
        self.assertEqual(result["status"], "skipped")

    def test_ambiguous_question_is_uncertain(self):
        result = detect_subject("Explain inheritance.")
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["subject"], "Uncertain")

    def test_empty_question_is_skipped(self):
        result = detect_subject("")
        self.assertEqual(result["status"], "skipped")


if __name__ == "__main__":
    unittest.main()

