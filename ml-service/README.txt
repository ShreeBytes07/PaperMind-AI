PaperMind AI ML starter files

Copy these files/folders into your existing PaperMind-AI project under ml-service.
Do not replace the whole project.

Train (run from project root):
  .\ml-service\.venv\Scripts\python.exe .\ml-service\training\train_model.py

Try one question:
  .\ml-service\.venv\Scripts\python.exe .\ml-service\predict.py

The CSV has 90 starter examples (3 per topic) covering all 30 internal topic labels.
This is only a baseline: results are not production-validated, and small-data scores can be misleading.
The Bloom labels are a starter subset, not all six levels; add reviewed examples including Evaluate.
PDF/image OCR, marks extraction, REST API integration, and MySQL persistence are not included yet.
