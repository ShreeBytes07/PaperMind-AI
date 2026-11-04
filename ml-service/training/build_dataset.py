from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "java_questions.csv"
OUTPUT = ROOT / "question_analysis_dataset.csv"

# Concept-specific supporting skills.
SUPPORT = {
    "2D Arrays": "Array indexing; nested loops",
    "Abstraction": "Abstract classes; abstract methods",
    "Arrays": "Indexing; iteration; element access",
    "Checked Exceptions": "try-catch; IOException",
    "Classes": "Fields; methods; class design",
    "Constructors": "Object initialization; parameters",
    "Data Types": "Primitive types; type selection",
    "Do-While Loop": "Loop conditions; input validation",
    "Dynamic Method Dispatch": "Inheritance; method overriding",
    "Encapsulation": "Access modifiers; data validation",
    "Exception Handling": "try-catch; exception types",
    "File System": "Paths; Files API; file operations",
    "Generic Classes": "Type parameters; type safety",
    "Inheritance": "Superclass; subclass; extends",
    "Java Commands": "JDK tools; compilation; execution",
    "Loops": "Iteration; termination conditions",
    "Methods": "Parameters; return values",
    "Object Class": "toString; equals; inheritance",
    "Object Cloning": "Object copying; shallow and deep copy",
    "Objects": "Instantiation; object state",
    "OOP Concepts": "Encapsulation; abstraction; inheritance; polymorphism",
    "Polymorphism": "Overloading; overriding",
    "Scanner": "Keyboard input; parsing",
    "Static Variables": "Class-level state; shared fields",
    "Strings": "String methods; immutability",
    "Threads": "Runnable; Thread; concurrency",
    "throw": "Exception creation; validation",
    "throws": "Method declarations; exception propagation",
    "Unchecked Exceptions": "Runtime exceptions; null references",
    "While Loop": "Loop conditions; iteration",
}

def analyse(row):
    question = str(row["question"]).strip()
    topic = str(row["topic"]).strip()
    difficulty = str(row["difficulty"]).strip().lower()
    bloom = str(row["bloom"]).strip()

    q = question.lower()

    # Identify the question's likely task from its wording.
    if any(word in q for word in [
        "write code", "write a", "create ", "implement ",
        "design ", "override ", "use a ", "use throw",
        "declare a", "read a file", "check whether",
        "find the", "calculate the", "trace "
    ]):
        question_type = "Code or application"
    elif any(word in q for word in [
        "differentiate", "compare ", "difference between",
        "shallow and deep", "compile-time and runtime"
    ]):
        question_type = "Comparison"
    elif any(word in q for word in [
        "explain", "why ", "how "
    ]):
        question_type = "Explanation"
    else:
        question_type = "Concept identification"

    if difficulty == "easy":
        difficulty_reason = (
            "Generally requires a basic definition, recognition, "
            "or a short familiar operation; confirm against the full task."
        )
        suggested_marks = "1-2"
        marks_reason = (
            "A short answer may suit 1-2 marks; the actual rubric "
            "and required detail determine the final marks."
        )
    elif difficulty == "medium":
        difficulty_reason = (
            "Generally requires explanation, comparison, tracing, "
            "or combining concepts; verify the actual steps required."
        )
        suggested_marks = "3-5"
        marks_reason = (
            "An explanation or short code task may suit 3-5 marks, "
            "depending on completeness and the marking rubric."
        )
    else:
        difficulty_reason = (
            "The starter label is hard; verify whether the question "
            "really requires multiple reasoning or implementation steps."
        )
        suggested_marks = "5-10"
        marks_reason = (
            "A multi-step solution may suit 5-10 marks; this is only "
            "an estimate until the question paper's rubric is known."
        )

    # Keep the original label for model compatibility.
    # A topic label is not necessarily the exact main concept.
    return {
        "question": question,
        "topic": topic,
        "difficulty": difficulty,
        "bloom": bloom,
        "main_concept": topic,
        "supporting_concepts": SUPPORT.get(topic, ""),
        "difficulty_reason": difficulty_reason,
        "suggested_marks": suggested_marks,
        "marks_reason": marks_reason,
        "question_type": question_type,
    }

def main():
    df = pd.read_csv(SOURCE).dropna(
        subset=["question", "topic", "difficulty", "bloom"]
    )

    required = {"question", "topic", "difficulty", "bloom"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(df.columns))}")

    result = pd.DataFrame(analyse(row) for _, row in df.iterrows())
    result.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("Created:", OUTPUT)
    print("Questions:", len(result))
    print("Topics:", result["topic"].nunique())
    print("Blank analysis fields:",
          int(result[[
              "main_concept", "supporting_concepts",
              "difficulty_reason", "suggested_marks",
              "marks_reason", "question_type"
          ]].isna().sum().sum()))
    print("\nQuestions per topic:")
    print(result.groupby("topic").size().to_string())
    print("\nPreview:")
    print(result[[
        "question", "main_concept", "difficulty",
        "difficulty_reason", "bloom", "suggested_marks"
    ]].head(5).to_string(index=False))

if __name__ == "__main__":
    main()