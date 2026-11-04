import re

JAVA_MARKERS = [
    r"\bjava\b",
    r"\bjvm\b",
    r"\bjdk\b",
    r"\bjre\b",
    r"\bjava\.lang\b",
    r"\bjava\.util\b",
    r"\bjava\.io\b",
    r"\bsystem\.out\.print(?:ln)?\b",
    r"\bpublic\s+static\s+void\s+main\b",
    r"\bstring\[\]\s+args\b",
    r"\bnew\s+scanner\b",
    r"\bimplements\s+\w+",
    r"\bextends\s+\w+",
    r"\bthrows\s+\w+",
    r"\bthrow\s+new\b",
    r"\bpublic\s+class\b",
]

NON_JAVA_MARKERS = {
    "Python": [
        r"\bpython\b", r"\bdef\s+\w+\s*\(",
        r"\bself\.", r"\belif\b", r"\bpandas\b", r"\bnumpy\b"
    ],
    "SQL/DBMS": [
        r"\bsql\b", r"\bdbms\b",
        r"\bselect\s+.+\s+from\b",
        r"\binsert\s+into\b", r"\bcreate\s+table\b",
        r"\bprimary key\b", r"\bforeign key\b",
        r"\bnormalization\b"
    ],
    "C/C++": [
        r"\bc\+\+\b", r"\blanguage\s+c\b", r"\bin c\b", r"\bc\s+program\b",
        r"\bprintf\s*\(", r"\bscanf\s*\(",
        r"\b#include\s*<", r"\bstd::",
        r"\bcout\s*<<", r"\bcin\s*>>"
    ],
}


def normalize(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def detect_subject(question):
    if not isinstance(question, str) or not question.strip():
        return {
            "subject": "Uncertain",
            "status": "skipped",
            "reason": "Empty question or invalid input."
        }

    q = normalize(question)

    non_java_matches = [
        subject
        for subject, patterns in NON_JAVA_MARKERS.items()
        if any(re.search(pattern, q) for pattern in patterns)
    ]

    java_match = any(
        re.search(pattern, q) for pattern in JAVA_MARKERS
    )

    if java_match and not non_java_matches:
        return {
            "subject": "Java",
            "status": "accepted",
            "reason": "Java-specific keyword or syntax detected."
        }

    if non_java_matches and not java_match:
        return {
            "subject": "Non-Java",
            "status": "skipped",
            "reason": "Detected: " + ", ".join(non_java_matches)
        }

    if java_match and non_java_matches:
        return {
            "subject": "Uncertain",
            "status": "skipped",
            "reason": "Conflicting subject indicators detected."
        }

    return {
        "subject": "Uncertain",
        "status": "skipped",
        "reason": "Not enough subject-specific evidence."
    }


