from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "training" / "java_questions.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA).dropna()
expected = {"question", "topic", "difficulty", "bloom"}
if not expected.issubset(df.columns):
    raise ValueError(f"CSV needs columns: {sorted(expected)}")

def make_model():
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
        ("classifier", LinearSVC())
    ])

for label in ["topic", "difficulty", "bloom"]:
    X, y = df["question"].astype(str), df[label].astype(str)
    # Split only if each class has enough examples for stratification.
    _, counts = y.factorize(), y.value_counts()
    can_stratify = counts.min() >= 2 and counts.size >= 2
    if can_stratify:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.40, random_state=42, stratify=y
        )
        evaluation_model = make_model().fit(X_train, y_train)
        pred = evaluation_model.predict(X_test)
        print(f"\\n=== {label.upper()} held-out evaluation ===")
        print("Accuracy:", round(float(accuracy_score(y_test, pred)), 3))
        print(classification_report(y_test, pred, zero_division=0))
    else:
        print(f"Skipping held-out evaluation for {label}: not enough examples per class.")
    final_model = make_model().fit(X, y)
    joblib.dump(final_model, MODEL_DIR / f"{label}_model.joblib")

metadata = {
    "training_rows": int(len(df)),
    "topic_count": int(df["topic"].nunique()),
    "note": "Small starter dataset. Evaluation is preliminary; predictions are not production-validated."
}
(MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(f"\\nSaved models in {MODEL_DIR}")
print("Reminder: expand and human-review the dataset before relying on results.")

