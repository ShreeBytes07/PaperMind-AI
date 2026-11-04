import re
from typing import Any


QUESTION_START = re.compile(
    r"^\s*(?:question\s*|q\s*)?(\d{1,3})\s*[.)]\s+(.+?)\s*$",
    re.IGNORECASE
)

QUESTION_WORD_START = re.compile(
    r"^\s*(?:question|q)\s*(\d{1,3})\s*[:.)-]\s*(.+?)\s*$",
    re.IGNORECASE
)

SUBQUESTION_START = re.compile(
    r"^\s*(?:\([a-h]\)|[a-h][.)]|\([ivx]+\))\s+",
    re.IGNORECASE
)

OPTION_START = re.compile(
    r"^\s*(?:\([a-d]\)|[a-d][.)])\s+",
    re.IGNORECASE
)

QUESTION_CUE = re.compile(
    r"^\s*(?:what|why|how|when|where|which|who|define|"
    r"explain|describe|discuss|write|list|state|compare|"
    r"differentiate|illustrate|prove|calculate|evaluate)\b",
    re.IGNORECASE
)


def _clean_lines(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.split("\n")
    ]


def _is_new_question(line: str) -> tuple[bool, str | None, str]:
    match = QUESTION_WORD_START.match(line)

    if match:
        return True, match.group(1), match.group(2).strip()

    match = QUESTION_START.match(line)

    if match:
        return True, match.group(1), match.group(2).strip()

    return False, None, line.strip()


def _numbered_extraction(lines: list[str]) -> list[dict[str, Any]]:
    questions = []
    current_number = None
    current_lines = []

    for line in lines:
        is_start, number, content = _is_new_question(line)

        if is_start:
            if current_number is not None and current_lines:
                questions.append({
                    "question_number": current_number,
                    "question_text": "\n".join(current_lines).strip()
                })

            current_number = number
            current_lines = [content]
        elif current_number is not None:
            current_lines.append(line)

    if current_number is not None and current_lines:
        questions.append({
            "question_number": current_number,
            "question_text": "\n".join(current_lines).strip()
        })

    return questions


def _paragraph_fallback(lines: list[str]) -> list[dict[str, Any]]:
    paragraphs = []
    current = []

    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
        else:
            current.append(line)

    if current:
        paragraphs.append(" ".join(current).strip())

    questions = []

    for paragraph in paragraphs:
        if len(paragraph) < 15:
            continue

        if paragraph.endswith("?") or QUESTION_CUE.match(paragraph):
            questions.append({
                "question_number": str(len(questions) + 1),
                "question_text": paragraph
            })

    return questions


def extract_questions(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        return {
            "status": "failed",
            "method": "none",
            "confidence": 0.0,
            "total_questions": 0,
            "questions": [],
            "message": "No readable text was supplied."
        }

    lines = _clean_lines(text)
    questions = _numbered_extraction(lines)

    # Numbered extraction is accepted only when it finds distinct,
    # non-empty question bodies. Do not split on numbers inside sentences.
    unique_numbers = {
        item["question_number"] for item in questions
    }

    if len(questions) >= 2 and len(unique_numbers) == len(questions):
        return {
            "status": "extracted",
            "method": "line_numbered",
            "confidence": 0.85,
            "total_questions": len(questions),
            "questions": questions,
            "message": "Numbered questions were detected."
        }

    if len(questions) == 1:
        question_text = questions[0]["question_text"]

        if question_text.endswith("?") or QUESTION_CUE.match(question_text):
            return {
                "status": "extracted_with_review",
                "method": "line_numbered",
                "confidence": 0.65,
                "total_questions": 1,
                "questions": questions,
                "message": "One numbered question was detected. Please review it."
            }

    fallback = _paragraph_fallback(lines)

    if fallback:
        return {
            "status": "extracted_with_review",
            "method": "paragraph_fallback",
            "confidence": 0.45,
            "total_questions": len(fallback),
            "questions": fallback,
            "message": "Possible questions were detected. Please review them."
        }

    return {
        "status": "uncertain",
        "method": "none",
        "confidence": 0.0,
        "total_questions": 0,
        "questions": [],
        "message": "Question boundaries could not be identified reliably."
    }
