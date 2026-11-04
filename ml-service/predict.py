
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"


# ============================================================
# TOPIC SUPPORT
# ============================================================

SUPPORT = {
    "Java Commands": ["Java syntax", "Main method", "Output statements"],
    "Data Types": ["Primitive types", "Reference types", "Type conversion"],
    "Operators": ["Increment and decrement", "Expression evaluation", "Assignment"],
    "Scanner": ["User input", "Scanner methods", "Input parsing"],
    "Loops": ["Iteration", "Loop condition", "Loop control"],
    "While Loop": ["Initialization", "Loop condition", "Iteration"],
    "Do-While Loop": ["Initialization", "Loop condition", "Iteration"],
    "Classes": ["Class declaration", "Fields", "Methods"],
    "Objects": ["Object creation", "Instance variables", "Object methods"],
    "Constructors": ["Object initialization", "Constructor parameters"],
    "Methods": ["Method declaration", "Parameters", "Return values"],
    "Object Class": ["toString()", "equals()", "Object methods"],
    "Static Variables": ["Class variables", "Static members", "Shared state"],
    "Arrays": ["Array declaration", "Array elements", "Indexing"],
    "2D Arrays": ["Rows and columns", "Nested loops", "Matrix indexing"],
    "OOP Concepts": ["Encapsulation", "Inheritance", "Polymorphism", "Abstraction"],
    "Encapsulation": ["Data hiding", "Access modifiers", "Getters and setters"],
    "Abstraction": ["Abstract classes", "Interfaces", "Implementation hiding"],
    "Inheritance": ["Superclass", "Subclass", "Method reuse"],
    "Polymorphism": ["Overloading", "Overriding", "Dynamic binding"],
    "Dynamic Method Dispatch": ["Runtime binding", "Method overriding"],
    "Object Cloning": ["clone()", "Cloneable", "Object copying"],
    "Exception Handling": ["try-catch", "finally", "Exception propagation"],
    "Checked Exceptions": ["Compile-time checking", "try-catch", "throws"],
    "Unchecked Exceptions": ["Runtime exceptions", "RuntimeException"],
    "throw": ["Exception creation", "Exception propagation"],
    "throws": ["Method declaration", "Exception propagation"],
    "Threads": ["Thread creation", "Concurrency", "Thread execution"],
    "File System": ["File reading", "File writing", "Resource management"],
    "Generic Classes": ["Type parameters", "Generic types", "Type safety"],
    "Strings": ["String methods", "String comparison", "Immutability"],
    "General Java": ["Java syntax", "Program logic", "Core Java concepts"],
}


def normalize(question):
    return re.sub(r"\s+", " ", str(question).strip().lower())


def matches_any(text, patterns):
    return any(re.search(pattern, text, re.I) for pattern in patterns)


def has(text, *patterns):
    return matches_any(text, list(patterns))


# ============================================================
# OUTPUT TRACING DETECTION
# ============================================================

def is_output_tracing(question):
    q = normalize(question)

    asks_output = has(
        q,
        r"\bfind the output\b",
        r"\bwhat is the output\b",
        r"\boutput of\b",
        r"\btrace the\b",
        r"\btrace this\b",
        r"\bshow the output\b",
        r"\bdetermine the output\b",
    )

    has_code = has(
        q,
        r"\bsystem\.out\.println\b",
        r"\bint\s+\w+\s*=",
        r"\bprint\s*\(",
    )

    return asks_output or (has_code and has(q, r"\boutput\b"))


# ============================================================
# TOPIC RULES
# Specific topics before general topics.
# ============================================================

TOPIC_RULES = [
    ("File System", [
        r"\bfile system\b", r"\bfile handling\b", r"\bfile operations?\b",
        r"\bfile reading\b", r"\bfile writing\b",
        r"\bread .{0,35} from (?:a |the )?file\b",
        r"\bwrite .{0,35} to (?:a |the )?file\b",
        r"\bfileinputstream\b", r"\bfileoutputstream\b",
        r"\bfilereader\b", r"\bfilewriter\b",
        r"\bbufferedreader\b", r"\bbufferedwriter\b",
        r"\bjava\.io\b", r"\bjava\.nio\.file\b",
        r"\bfiles?\.readall", r"\bpath\.of\s*\(",
    ]),
    ("Dynamic Method Dispatch", [
        r"\bdynamic method dispatch\b", r"\bruntime method dispatch\b",
    ]),
    ("Unchecked Exceptions", [
        r"\bunchecked exceptions?\b", r"\bruntime exceptions?\b",
    ]),
    ("Checked Exceptions", [
        r"\bchecked exceptions?\b", r"\bthrows clause\b",
        r"\bdeclare exceptions?\b",
    ]),
    ("Do-While Loop", [r"\bdo[\s-]*while\b"]),
    ("While Loop", [r"\bwhile loop\b", r"\bwhile statement\b"]),
    ("2D Arrays", [
        r"\b2[\s-]*d arrays?\b", r"\btwo[\s-]*dimensional arrays?\b",
        r"\bmatrix\b", r"\brows and columns\b",
    ]),
    ("Object Cloning", [
        r"\bobject cloning\b", r"\bclone\s*\(\s*\)", r"\bcloneable\b",
    ]),
    ("Static Variables", [
        r"\bstatic variables?\b", r"\bstatic members?\b",
        r"\bstatic keyword\b",
    ]),
    ("Generic Classes", [
        r"\bgeneric classes?\b", r"\bgenerics\b", r"\btype parameters\b",
    ]),
    ("Encapsulation", [
        r"\bencapsulation\b", r"\bdata hiding\b",
        r"\bgetters? and setters?\b",
    ]),
    ("Abstraction", [
        r"\babstraction\b", r"\babstract classes?\b", r"\binterfaces?\b",
    ]),
    ("Inheritance", [
        r"\binheritance\b", r"\bsuperclass\b", r"\bsubclass\b",
        r"\bextends keyword\b",
    ]),
    ("Polymorphism", [
        r"\bpolymorphism\b", r"\bmethod overloading\b",
        r"\bmethod overriding\b", r"\boverloading\b", r"\boverriding\b",
    ]),
    ("Constructors", [
        r"\bconstructors?\b", r"\bparameterized constructor\b",
        r"\bdefault constructor\b",
    ]),
    ("Object Class", [
        r"\bobject class\b", r"\btostring\s*\(",
        r"\bequals\s*\(", r"\bhashcode\s*\(",
    ]),
    ("Exception Handling", [
        r"\bexception handling\b", r"\btry[\s-]*catch\b",
        r"\bfinally block\b", r"\bexception\b",
    ]),
    ("throw", [
        r"\bthrow keyword\b", r"\bthrow an exception\b",
        r"\bthrow statement\b",
    ]),
    ("throws", [
        r"\bthrows keyword\b", r"\bthrows clause\b",
    ]),
    ("Threads", [
        r"\bmultithreading\b", r"\bthread class\b",
        r"\brunnable\b", r"\bthreads?\b",
    ]),
    ("Scanner", [
        r"\bscanner\b", r"\bnextint\s*\(", r"\bnextline\s*\(",
        r"\bnextdouble\s*\(", r"\buser input\b",
    ]),
    ("Operators", [
        r"\bincrement operators?\b", r"\bdecrement operators?\b",
        r"\bpost[\s-]*increment\b", r"\bpre[\s-]*increment\b",
        r"\bpost[\s-]*decrement\b", r"\bpre[\s-]*decrement\b",
        r"\boperators?\b",
    ]),
    ("Arrays", [
        r"\barrays?\b", r"\barray elements?\b", r"\barray indexing\b",
    ]),
    ("Strings", [
        r"\bstrings?\b", r"\bstring methods?\b",
        r"\bstring comparison\b", r"\bstring manipulation\b",
    ]),
    ("Data Types", [
        r"\bdata types?\b", r"\bprimitive types?\b",
        r"\btype conversion\b", r"\btype casting\b",
    ]),
    ("Objects", [
        r"\bobjects?\b", r"\bobject creation\b", r"\bnew keyword\b",
    ]),
    ("Classes", [r"\bclasses\b", r"\bclass declaration\b"]),
    ("Methods", [
        r"\bmethods?\b", r"\breturn type\b", r"\bmethod declaration\b",
    ]),
    ("Loops", [
        r"\bfor loop\b", r"\blooping statements?\b",
        r"\biteration\b", r"\bwhile and for\b",
    ]),
    ("Java Commands", [
        r"\bmain method\b", r"\bjava commands?\b",
    ]),
]


def rule_based_topic(question):
    q = normalize(question)

    # Classify output-tracing questions by the actual code subject.
    if is_output_tracing(q):
        if has(q, r"\bdo[\s-]*while\b"):
            return "Do-While Loop"
        if has(q, r"\bwhile\b"):
            return "While Loop"
        if has(q, r"\bfor\b"):
            return "Loops"
        if has(q, r"\barray\b"):
            return "Arrays"
        if has(q, r"\bstring\b"):
            return "Strings"
        if has(q, r"\bscanner\b", r"\bnextint\s*\(", r"\bnextline\s*\("):
            return "Scanner"
        if has(q, r"\+\+", r"--",
               r"\bpost[\s-]*increment\b", r"\bpre[\s-]*increment\b",
               r"\bpost[\s-]*decrement\b", r"\bpre[\s-]*decrement\b"):
            return "Operators"

    for topic, patterns in TOPIC_RULES:
        if matches_any(q, patterns):
            return topic

    return None


def load_model(filename):
    path = MODEL_DIR / filename
    if not path.exists():
        return None
    try:
        import joblib
        return joblib.load(path)
    except Exception:
        return None


def classify_topic(question):
    topic = rule_based_topic(question)
    if topic:
        return topic

    model = load_model("topic_model.joblib")
    if model is not None:
        try:
            prediction = model.predict([question])[0]
            if prediction in SUPPORT:
                return prediction
        except Exception:
            pass

    return "General Java"


# ============================================================
# QUESTION TYPE
# ============================================================

def classify_question_type(question):
    q = normalize(question)

    if has(q, r"\bdifferentiate\b", r"\bcompare\b",
           r"\bdifference between\b", r"\bdistinguish between\b"):
        return "Comparison"

    if is_output_tracing(q):
        return "Output tracing"

    if has(
        q,
        r"\bwrite (?:a |an )?(?:java )?program\b",
        r"\bwrite (?:a )?program in java\b",
        r"\bwrite (?:a )?(?:java )?constructor\b",
        r"\bwrite code\b", r"\bimplement\b",
        r"\bdevelop a program\b", r"\bcode to\b",
    ):
        return "Code or application"

    if has(q, r"\bdefine\b", r"\bwhat is\b", r"\bwhat are\b",
           r"\bname the\b", r"\blist the\b"):
        return "Definition or identification"

    if has(q, r"\bexplain\b", r"\bdescribe\b", r"\bhow does\b",
           r"\bhow do\b", r"\bhow to\b", r"\bwhy\b"):
        return "Explanation"

    return "Conceptual question"


# ============================================================
# BLOOM'S TAXONOMY
# ============================================================

def infer_bloom(question, question_type):
    q = normalize(question)

    if has(q, r"\bcritically assess\b", r"\bevaluate\b",
           r"\bjustify\b", r"\bjudge whether\b"):
        return "Evaluate"

    if has(q, r"\bdesign\b", r"\bcreate\b", r"\bpropose\b",
           r"\bdevelop a new\b"):
        return "Create"

    if question_type in ("Output tracing", "Comparison"):
        return "Analyze"

    if question_type == "Code or application":
        return "Apply"

    if has(q, r"\banalyze\b", r"\banalyse\b", r"\bexamine\b",
           r"\btrace\b", r"\bdetermine why\b"):
        return "Analyze"

    if question_type == "Definition or identification":
        return "Remember"

    if question_type == "Explanation":
        return "Understand"

    return "Understand"


# ============================================================
# CONCEPT DETECTION
# Weights indicate relative keyword evidence, not probabilities.
# ============================================================

CONCEPT_PATTERNS = [
    ("Post-increment", [
        r"\b\w+\s*\+\+", r"\bpost[\s-]*increment\b",
    ]),
    ("Pre-increment", [
        r"\+\+\s*\w+\b", r"\bpre[\s-]*increment\b",
    ]),
    ("Post-decrement", [
        r"\b\w+\s*--", r"\bpost[\s-]*decrement\b",
    ]),
    ("Pre-decrement", [
        r"--\s*\w+\b", r"\bpre[\s-]*decrement\b",
    ]),
    ("Assignment", [
        r"\b\w+\s*=(?!=)",
    ]),
    ("Arithmetic Operators", [
        r"[+\-*/%]", r"\barithmetic operators?\b",
    ]),
    ("File Operations", [
        r"\bfile system\b", r"\bfile handling\b",
        r"\bfile operations?\b", r"\bfile reading\b",
        r"\bfile writing\b",
        r"\bread .{0,35} from (?:a |the )?file\b",
        r"\bwrite .{0,35} to (?:a |the )?file\b",
        r"\bfileinputstream\b", r"\bfileoutputstream\b",
        r"\bfilereader\b", r"\bfilewriter\b",
        r"\bbufferedreader\b", r"\bbufferedwriter\b",
        r"\bjava\.io\b", r"\bjava\.nio\.file\b",
    ]),
    ("BufferedReader", [r"\bbufferedreader\b", r"\breadline\s*\("]),
    ("BufferedWriter", [r"\bbufferedwriter\b"]),
    ("Scanner", [
        r"\bscanner\b", r"\bnextint\s*\(", r"\bnextline\s*\(",
        r"\bnextdouble\s*\(",
    ]),
    ("Constructor", [
        r"\bconstructors?\b", r"\bparameterized constructor\b",
        r"\bdefault constructor\b",
    ]),
    ("Constructor Parameters", [
        r"\bparameterized constructor\b",
        r"\bconstructor parameters?\b",
        r"\bconstructor that initializes\b",
    ]),
    ("Object Initialization", [
        r"\bobject initialization\b", r"\binitialize an object\b",
        r"\binitializes? (?:the )?(?:object|fields?|variables?)\b",
    ]),
    ("Inheritance", [
        r"\binheritance\b", r"\bsuperclass\b", r"\bsubclass\b",
        r"\bextends\b",
    ]),
    ("Method Reuse", [
        r"\bmethod reuse\b", r"\breuse (?:of )?(?:methods?|code)\b",
    ]),
    ("Exception Handling", [
        r"\bexception handling\b", r"\btry[\s-]*catch\b",
        r"\bcatch\s*\(", r"\bfinally block\b", r"\bioexception\b",
    ]),
    ("Resource Management", [
        r"\btry[\s-]*with[\s-]*resources\b",
        r"\bresource management\b", r"\bclose the file\b",
        r"\bclose the reader\b",
    ]),
    ("Iteration", [
        r"\bloop\b", r"\biteration\b", r"\biterate\b", r"\brepeatedly\b",
    ]),
    ("Loop Condition", [
        r"\bloop condition\b", r"\bcondition\b",
        r"\bwhile\b", r"\bfor loop\b",
    ]),
    ("Initialization", [
        r"\binitialization\b", r"\binitialize\b",
        r"\binitializes\b", r"\bstarting value\b",
    ]),
    ("Array Indexing", [
        r"\barray indexing\b", r"\barray index\b",
        r"\bindex position\b", r"\bindex out of bounds\b",
    ]),
    ("Array Processing", [
        r"\barrays?\b", r"\barray elements?\b",
    ]),
    ("Method Overriding", [
        r"\bmethod overriding\b", r"\boverride\b",
    ]),
    ("Method Overloading", [
        r"\bmethod overloading\b", r"\boverload\b",
    ]),
    ("Exception Declaration", [
        r"\bthrows\b", r"\bthrow\b",
    ]),
    ("Threading", [
        r"\bmultithreading\b", r"\bthread class\b", r"\brunnable\b",
    ]),
    ("String Processing", [
        r"\bstring methods?\b", r"\bstring comparison\b",
        r"\bstring manipulation\b",
    ]),
    ("Class Structure", [
        r"\bclass declaration\b", r"\bclass structure\b",
        r"\bfields and methods\b",
    ]),
    ("Polymorphism", [
        r"\bpolymorphism\b", r"\bdynamic binding\b",
    ]),
    ("Encapsulation", [
        r"\bencapsulation\b", r"\bdata hiding\b",
        r"\bgetters? and setters?\b",
    ]),
    ("Abstraction", [
        r"\babstraction\b", r"\babstract class\b", r"\binterface\b",
    ]),
]


def extract_concepts(question):
    q = normalize(question)
    found = []

    for concept, patterns in CONCEPT_PATTERNS:
        if matches_any(q, patterns):
            found.append(concept)

    if not found:
        return []

    weight = round(1.0 / len(found), 2)
    results = [
        {"concept": concept, "weight": weight}
        for concept in found
    ]

    results[-1]["weight"] = round(
        results[-1]["weight"] + 1.0 - sum(x["weight"] for x in results),
        2,
    )
    return results


# ============================================================
# SUPPORTING CONCEPTS
# ============================================================

def get_supporting_concepts(question, topic):
    q = normalize(question)

    if topic == "Operators":
        concepts = ["Expression evaluation"]

        if has(q, r"\+\+", r"\bpost[\s-]*increment\b"):
            concepts.append("Increment operator")
        if has(q, r"--", r"\bdecrement\b"):
            concepts.append("Decrement operator")
        if has(q, r"\bint\b", r"\bdouble\b", r"\bfloat\b"):
            concepts.append("Variable values")

        return list(dict.fromkeys(concepts))

    if topic == "File System":
        concepts = ["File handling"]

        if has(q, r"\bread\b", r"\bbufferedreader\b", r"\bfilereader\b",
               r"\bfileinputstream\b"):
            concepts.append("File reading")

        if has(q, r"\bwrite\b", r"\bbufferedwriter\b", r"\bfilewriter\b",
               r"\bfileoutputstream\b"):
            concepts.append("File writing")

        if "bufferedreader" in q:
            concepts.append("BufferedReader")
        if "bufferedwriter" in q:
            concepts.append("BufferedWriter")

        if has(q, r"\bclose\b", r"\bresource management\b",
               r"\btry[\s-]*with[\s-]*resources\b"):
            concepts.append("Resource management")

        if has(q, r"\bexception\b", r"\bioexception\b",
               r"\btry\b", r"\bcatch\b", r"\bthrows\b"):
            concepts.append("Exception handling")

        return list(dict.fromkeys(concepts))

    if topic == "Constructors":
        concepts = ["Object initialization"]

        if has(q, r"\bparameterized\b", r"\bparameters?\b",
               r"\bproduct id\b", r"\bproduct name\b", r"\bname\b"):
            concepts.append("Constructor parameters")

        if has(q, r"\bdefault constructor\b"):
            concepts.append("Default constructor")
        if has(q, r"\bparameterized constructor\b"):
            concepts.append("Parameterized constructor")

        return list(dict.fromkeys(concepts))

    if topic == "Scanner":
        concepts = ["User input"]

        if has(q, r"\bnextint\b", r"\bnextline\b", r"\bnextdouble\b",
               r"\bscanner methods?\b"):
            concepts.append("Scanner methods")

        if has(q, r"\bparse\b", r"\binput parsing\b", r"\bconvert\b"):
            concepts.append("Input parsing")

        return concepts

    if topic == "Inheritance":
        concepts = []

        if has(q, r"\bsuperclass\b"):
            concepts.append("Superclass")
        if has(q, r"\bsubclass\b"):
            concepts.append("Subclass")
        if has(q, r"\breuse\b", r"\binherited methods?\b"):
            concepts.append("Method reuse")

        return concepts or SUPPORT[topic]

    return SUPPORT.get(topic, SUPPORT["General Java"])


# ============================================================
# DIFFICULTY AND MARKS
# ============================================================

def analyse_difficulty_and_marks(question, topic, question_type, bloom):
    q = normalize(question)

    if question_type == "Output tracing":
        if has(q, r"\+\+", r"--", r"\bpost[\s-]*increment\b",
               r"\bpre[\s-]*increment\b"):
            return {
                "difficulty": "easy",
                "difficulty_reason": (
                    "The code contains a single increment or decrement "
                    "operation. The learner must identify the value used "
                    "by the expression and the variable's subsequent value; "
                    "no loop or multi-step control flow is present."
                ),
                "suggested_marks": "1-2",
                "marks_reason": (
                    "Marks can cover the printed value and the variable's "
                    "updated value after expression evaluation."
                ),
            }

        if has(q, r"\bwhile\b", r"\bfor\b", r"\bdo[\s-]*while\b"):
            return {
                "difficulty": "medium",
                "difficulty_reason": (
                    "The output depends on execution order, loop conditions, "
                    "and variable changes across iterations."
                ),
                "suggested_marks": "2-4",
                "marks_reason": (
                    "Marks can cover execution steps, intermediate values, "
                    "loop termination, and the final output."
                ),
            }

        return {
            "difficulty": "easy",
            "difficulty_reason": (
                "The task asks for the result of a code expression or "
                "short sequence of statements."
            ),
            "suggested_marks": "1-3",
            "marks_reason": (
                "Marks can cover the relevant evaluation steps and "
                "the final output."
            ),
        }

    if topic == "Constructors":
        if question_type == "Code or application":
            return {
                "difficulty": "easy",
                "difficulty_reason": (
                    "The task requires one constructor with parameters "
                    "and assignments to product ID and name fields. "
                    "No inheritance or validation logic is requested."
                ),
                "suggested_marks": "3-4",
                "marks_reason": (
                    "Marks can cover the constructor signature, parameters, "
                    "correct field assignments, and valid syntax."
                ),
            }

        if question_type == "Comparison":
            return {
                "difficulty": "medium",
                "difficulty_reason": (
                    "The answer must distinguish constructor behavior, "
                    "parameter requirements, and initialization values."
                ),
                "suggested_marks": "3-5",
                "marks_reason": (
                    "Marks can cover both definitions, their differences, "
                    "and suitable examples."
                ),
            }

        if has(q, r"\bwhat is\b", r"\bpurpose of\b", r"\bdefine\b"):
            return {
                "difficulty": "easy",
                "difficulty_reason": (
                    "The question asks for the constructor's purpose "
                    "and its role in object initialization."
                ),
                "suggested_marks": "1-2",
                "marks_reason": (
                    "Marks can cover the definition and role during "
                    "object creation."
                ),
            }

    if topic == "Scanner":
        if question_type in ("Explanation", "Definition or identification"):
            return {
                "difficulty": "easy",
                "difficulty_reason": (
                    "The question asks about Scanner's basic role in "
                    "receiving user input, without requiring a complete "
                    "program or input-validation logic."
                ),
                "suggested_marks": "2-3",
                "marks_reason": (
                    "Marks can cover Scanner's purpose, System.in, and "
                    "a relevant input method."
                ),
            }

    if topic == "File System":
        if question_type == "Code or application":
            return {
                "difficulty": "medium",
                "difficulty_reason": (
                    "A file-reading program must choose an appropriate API, "
                    "open and read the file, and handle resource lifetime "
                    "and possible I/O errors."
                ),
                "suggested_marks": "4-6",
                "marks_reason": (
                    "Marks can cover imports, opening and reading the file, "
                    "correct output, exception handling, and resource closing."
                ),
            }

        return {
            "difficulty": "easy" if question_type == "Explanation" else "medium",
            "difficulty_reason": (
                "The question asks for the steps involved in accessing "
                "file contents without requiring a complete implementation."
            ),
            "suggested_marks": "3-5",
            "marks_reason": (
                "Marks can cover an appropriate file API, reading steps, "
                "resource handling, and an example."
            ),
        }

    if topic == "Inheritance":
        if question_type == "Code or application":
            return {
                "difficulty": "easy",
                "difficulty_reason": (
                    "A basic demonstration can use one superclass, one "
                    "subclass, extends, and an inherited method. Complex "
                    "hierarchies or overriding are not explicitly requested."
                ),
                "suggested_marks": "3-5",
                "marks_reason": (
                    "Marks can cover the superclass, subclass, inherited "
                    "method, and a working demonstration."
                ),
            }

        return {
            "difficulty": "easy",
            "difficulty_reason": (
                "A basic explanation can describe the superclass-subclass "
                "relationship and how inheritance supports code reuse."
            ),
            "suggested_marks": "2-3",
            "marks_reason": (
                "Marks can cover the definition, extends relationship, "
                "and an example."
            ),
        }

    if topic in ("Loops", "While Loop", "Do-While Loop"):
        if question_type == "Code or application":
            return {
                "difficulty": "medium",
                "difficulty_reason": (
                    "The program requires correct initialization, a valid "
                    "loop condition, variable updates, and termination."
                ),
                "suggested_marks": "3-5",
                "marks_reason": (
                    "Marks can cover initialization, condition, update "
                    "logic, loop body, and correct behavior."
                ),
            }

        return {
            "difficulty": "easy",
            "difficulty_reason": (
                "The question focuses on the loop's working principle "
                "or condition controlling repetition."
            ),
            "suggested_marks": "2-3",
            "marks_reason": (
                "Marks can cover the loop's purpose, condition, behavior, "
                "and a simple example."
            ),
        }

    if topic in ("Arrays", "2D Arrays"):
        return {
            "difficulty": "medium",
            "difficulty_reason": (
                "The answer requires explaining array organization and "
                "the indexing, traversal, or operation relevant to the task."
            ),
            "suggested_marks": "3-5",
            "marks_reason": (
                "Marks can cover array structure, indexing, the requested "
                "operation, and an example."
            ),
        }

    if topic in (
        "Exception Handling", "Checked Exceptions",
        "Unchecked Exceptions", "throw", "throws",
    ):
        return {
            "difficulty": "medium",
            "difficulty_reason": (
                "The answer requires explaining the exception mechanism, "
                "its syntax, and its effect on program execution."
            ),
            "suggested_marks": "3-5",
            "marks_reason": (
                "Marks can cover purpose, correct syntax or behavior, "
                "and a suitable example."
            ),
        }

    if question_type == "Comparison":
        return {
            "difficulty": "medium",
            "difficulty_reason": (
                "The answer requires describing both concepts and comparing "
                "their behavior, properties, or use cases."
            ),
            "suggested_marks": "3-5",
            "marks_reason": (
                "Marks can cover both definitions, key differences, "
                "and an example."
            ),
        }

    if question_type == "Code or application":
        return {
            "difficulty": "medium",
            "difficulty_reason": (
                "The solution requires translating the requirement into "
                "valid Java syntax and implementing the required logic."
            ),
            "suggested_marks": "3-6",
            "marks_reason": (
                "Marks can cover program structure, implementation logic, "
                "syntax, and expected behavior."
            ),
        }

    if question_type == "Definition or identification":
        return {
            "difficulty": "easy",
            "difficulty_reason": (
                "The question mainly tests recognition or explanation "
                "of one core Java concept."
            ),
            "suggested_marks": "1-2",
            "marks_reason": (
                "Marks can cover the definition, purpose, and one relevant "
                "property or example."
            ),
        }

    if question_type == "Explanation":
        return {
            "difficulty": "easy",
            "difficulty_reason": (
                "The question asks for a conceptual explanation rather "
                "than a program, output trace, or multi-concept comparison."
            ),
            "suggested_marks": "2-3",
            "marks_reason": (
                "Marks can cover the concept's meaning, working principle, "
                "and a relevant detail or example."
            ),
        }

    return {
        "difficulty": "medium",
        "difficulty_reason": (
            "The answer requires identifying the main Java concept "
            "and explaining its relevant behavior or relationship."
        ),
        "suggested_marks": "2-5",
        "marks_reason": (
            "Marks can cover the core explanation, important relationships, "
            "and an appropriate example."
        ),
    }


# ============================================================
# SCORE
# Heuristic rating, not a probability or model confidence.
# ============================================================

def calculate_score(
    question, topic, question_type, bloom,
    difficulty, suggested_marks, detected_concepts,
):
    q = normalize(question)

    complexity_scores = {"easy": 4.0, "medium": 6.5, "hard": 8.5}
    bloom_scores = {
        "Remember": 3.0, "Understand": 4.5, "Apply": 6.0,
        "Analyze": 7.5, "Evaluate": 8.5, "Create": 9.0,
    }
    marks_scores = {
        "1-2": 3.0, "1-3": 4.0, "2-3": 4.5, "2-4": 4.5,
        "3-4": 5.5, "3-5": 6.0, "3-6": 7.0, "4-6": 7.0,
    }
    structure_scores = {
        "Definition or identification": 4.0,
        "Explanation": 5.5,
        "Comparison": 6.5,
        "Output tracing": 7.0,
        "Code or application": 7.5,
        "Conceptual question": 5.0,
    }

    complexity = complexity_scores.get(difficulty, 5.5)
    bloom_score = bloom_scores.get(bloom, 5.0)
    marks_score = marks_scores.get(suggested_marks, 5.0)
    structure_score = structure_scores.get(question_type, 5.0)

    if has(q, r"\bwith example\b", r"\bdifferentiate\b",
           r"\bcompare\b", r"\bfind the output\b"):
        structure_score = min(10.0, structure_score + 1.0)

    count = len(detected_concepts)
    if count <= 1:
        diversity = 3.0
    elif count == 2:
        diversity = 5.0
    elif count == 3:
        diversity = 6.5
    else:
        diversity = min(9.0, 6.5 + 0.5 * (count - 3))

    components = {
        "Concept Complexity": round(complexity, 1),
        "Bloom's Taxonomy": round(bloom_score, 1),
        "Marks Weight": round(marks_score, 1),
        "Question Structure": round(structure_score, 1),
        "Concept Diversity": round(diversity, 1),
    }

    score = round(sum(components.values()) / len(components), 1)

    names = (
        ", ".join(item["concept"] for item in detected_concepts)
        if detected_concepts else topic
    )

    explanation = (
        f"The main concept is {topic}. Detected keyword concepts: {names}. "
        f"{_short_reason(difficulty, question_type, q)} "
        f"The Bloom level is {bloom}. The estimated mark range is "
        f"{suggested_marks}. The score is {score}/10, calculated as the "
        f"unweighted average of five heuristic components: complexity "
        f"{complexity:.1f}, Bloom level {bloom_score:.1f}, marks "
        f"{marks_score:.1f}, structure {structure_score:.1f}, and concept "
        f"diversity {diversity:.1f}. It is not a probability or model confidence."
    )

    return {
        "score": score,
        "score_out_of": 10,
        "score_breakdown": components,
        "analysis_explanation": explanation,
    }


def _short_reason(difficulty, question_type, q=""):
    if question_type == "Output tracing":
        if has(q, r"\+\+", r"--"):
            return (
                "The expression requires identifying the value used by "
                "the increment or decrement operation and the subsequent "
                "variable update."
            )
        if has(q, r"\bwhile\b", r"\bfor\b", r"\bdo[\s-]*while\b"):
            return (
                "The result depends on execution order, loop conditions, "
                "and variable changes across iterations."
            )
        return (
            "The task requires tracing the expression or statements "
            "to determine their result."
        )

    if question_type == "Code or application":
        return (
            "The task requires translating a requirement into Java code "
            "and implementing the required behavior."
        )

    if question_type == "Comparison":
        return (
            "The task requires identifying meaningful similarities "
            "or differences between concepts."
        )

    if difficulty == "easy":
        return "The task focuses on a limited concept and a direct explanation."

    if difficulty == "hard":
        return "The task requires multiple connected steps or substantial reasoning."

    return "The task requires connecting the main concept to its relevant behavior."


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyse_question(question):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string.")

    question = question.strip()
    topic = classify_topic(question)
    question_type = classify_question_type(question)
    bloom = infer_bloom(question, question_type)

    analysis = analyse_difficulty_and_marks(
        question, topic, question_type, bloom
    )
    concepts = extract_concepts(question)
    supporting = get_supporting_concepts(question, topic)

    score_data = calculate_score(
        question=question,
        topic=topic,
        question_type=question_type,
        bloom=bloom,
        difficulty=analysis["difficulty"],
        suggested_marks=analysis["suggested_marks"],
        detected_concepts=concepts,
    )

    return {
        "question": question,
        "main_concept": topic,
        "supporting_concepts": "; ".join(supporting),
        "detected_concepts": concepts,
        "difficulty": analysis["difficulty"],
        "difficulty_reason": analysis["difficulty_reason"],
        "bloom": bloom,
        "suggested_marks": analysis["suggested_marks"],
        "marks_reason": analysis["marks_reason"],
        "question_type": question_type,
        **score_data,
    }


# ============================================================
# REGRESSION TESTS
# ============================================================

def run_tests():
    test_cases = [
        {
            "question": "Write a Java program to read data from a file using BufferedReader.",
            "topic": "File System",
            "type": "Code or application",
            "bloom": "Apply",
        },
        {
            "question": "Explain how to read data from a file in Java.",
            "topic": "File System",
            "type": "Explanation",
            "bloom": "Understand",
        },
        {
            "question": "Write a Java program to find the output of a while loop.",
            "topic": "While Loop",
            "type": "Output tracing",
            "bloom": "Analyze",
        },
        {
            "question": "Explain how Scanner reads user input in Java.",
            "topic": "Scanner",
            "type": "Explanation",
            "bloom": "Understand",
        },
        {
            "question": "Differentiate a default constructor and a parameterized constructor.",
            "topic": "Constructors",
            "type": "Comparison",
            "bloom": "Analyze",
        },
        {
            "question": "Write a Java constructor that initializes product ID and name.",
            "topic": "Constructors",
            "type": "Code or application",
            "bloom": "Apply",
        },
        {
            "question": "What is the purpose of a constructor in Java?",
            "topic": "Constructors",
            "type": "Definition or identification",
            "bloom": "Remember",
        },
        {
            "question": "What is the output of this code: int x=5; System.out.println(x++);",
            "topic": "Operators",
            "type": "Output tracing",
            "bloom": "Analyze",
        },
        {
            "question": "Compare method overloading and method overriding in Java.",
            "topic": "Polymorphism",
            "type": "Comparison",
            "bloom": "Analyze",
        },
        {
            "question": "Write a Java program to demonstrate inheritance.",
            "topic": "Inheritance",
            "type": "Code or application",
            "bloom": "Apply",
        },
    ]

    failed = 0

    for case in test_cases:
        result = analyse_question(case["question"])

        checks = {
            "main_concept": case["topic"],
            "question_type": case["type"],
            "bloom": case["bloom"],
        }

        errors = [
            f"{field}: expected {expected!r}, got {result[field]!r}"
            for field, expected in checks.items()
            if result[field] != expected
        ]

        if case["type"] == "Output tracing" and "x++" in case["question"]:
            detected_names = [
                item["concept"] for item in result["detected_concepts"]
            ]
            if "Post-increment" not in detected_names:
                errors.append("Post-increment concept was not detected.")

        print("=" * 70)
        print("QUESTION:", case["question"])

        if errors:
            failed += 1
            print("TEST FAILED")
            for error in errors:
                print(" -", error)
        else:
            print("TEST PASSED")

        print("Topic:", result["main_concept"])
        print("Type:", result["question_type"])
        print("Bloom:", result["bloom"])
        print("Difficulty:", result["difficulty"])
        print("Marks:", result["suggested_marks"])
        print("Detected concepts:", result["detected_concepts"])

    print("=" * 70)
    print(f"Regression tests: {len(test_cases) - failed}/{len(test_cases)} passed")
    return failed == 0


if __name__ == "__main__":
    run_tests()
