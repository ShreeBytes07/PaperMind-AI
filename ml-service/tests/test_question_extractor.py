import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from question_extractor import extract_questions


class TestQuestionExtractor(unittest.TestCase):

    def test_twelve_numbered_questions(self):
        text = "\n".join(
            f"{i}. Explain concept number {i} with an example."
            for i in range(1, 13)
        )
        result = extract_questions(text)
        self.assertEqual(result["total_questions"], 12)
        self.assertEqual(result["status"], "extracted")

    def test_internal_numbers_do_not_split_question(self):
        text = (
            "1. Explain the range of numbers from 1 to 10 "
            "in a Java loop.\n"
            "2. What is inheritance in Java?"
        )
        result = extract_questions(text)
        self.assertEqual(result["total_questions"], 2)
        self.assertIn("from 1 to 10", result["questions"][0]["question_text"])

    def test_q_number_format(self):
        text = "Q1. What is a class?\nQ2. Explain an object."
        result = extract_questions(text)
        self.assertEqual(result["total_questions"], 2)

    def test_question_word_format(self):
        text = "Question 1: Define Java.\nQuestion 2: Explain JVM."
        result = extract_questions(text)
        self.assertEqual(result["total_questions"], 2)

    def test_options_remain_inside_question(self):
        text = (
            "1. Which is a Java keyword?\n"
            "a) class\nb) object\nc) file\nd) folder\n"
            "2. What is JVM?"
        )
        result = extract_questions(text)
        self.assertEqual(result["total_questions"], 2)
        self.assertIn("a) class", result["questions"][0]["question_text"])

    def test_empty_input(self):
        result = extract_questions("")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["total_questions"], 0)

    def test_unstructured_text_is_not_fabricated(self):
        result = extract_questions("This is ordinary text without questions.")
        self.assertEqual(result["total_questions"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
