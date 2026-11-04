from subject_detector import detect_subject

test_questions = [
    "Explain inheritance in Java.",
    "Write a Java program using arrays.",
    "What is the purpose of JVM?",
    "Explain Python decorators.",
    "What is normalization in DBMS?",
    "Write an SQL query to select all students.",
    "Explain printf and scanf in C.",
    "Explain inheritance.",
    "What is a primary key in DBMS?",
    "Explain inheritance in Python.",
    "Write a C program using printf.",
    "Write Java code to connect to MySQL.",
    "Explain polymorphism in Java with an example."
]

for question in test_questions:
    result = detect_subject(question)
    print("-" * 60)
    print("Question:", question)
    print("Subject:", result["subject"])
    print("Status:", result["status"])
    print("Reason:", result["reason"])
