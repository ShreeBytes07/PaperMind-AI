import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from predict import analyse_question
from question_extractor import extract_questions
from subject_detector import detect_subject


class MLRequestHandler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        response = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {
                "status": "ok",
                "service": "PaperMind AI ML Service"
            })
        else:
            self.send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        if self.path == "/extract":
            try:
                length = int(self.headers.get("Content-Length", "0"))

                if length <= 0 or length > 5_000_000:
                    self.send_json(400, {
                        "error": "Request body is missing or too large"
                    })
                    return

                body = self.rfile.read(length)
                payload = json.loads(body.decode("utf-8"))
                text = payload.get("text")

                if not isinstance(text, str) or not text.strip():
                    self.send_json(400, {
                        "error": "A non-empty text field is required"
                    })
                    return

                result = extract_questions(text)
                self.send_json(200, result)

            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_json(400, {
                    "error": "Invalid JSON request"
                })
            except Exception as error:
                print("[EXTRACTION API ERROR]", str(error))
                self.send_json(500, {
                    "error": "Question extraction failed"
                })

            return

        if self.path != "/analyze":
            self.send_json(404, {"error": "Endpoint not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > 100_000:
                self.send_json(400, {
                    "error": "Request body is missing or too large"
                })
                return

            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
            question = payload.get("question")

            if not isinstance(question, str) or not question.strip():
                self.send_json(400, {
                    "error": "A non-empty question is required"
                })
                return

            question = question.strip()
            subject_result = detect_subject(question)

            if subject_result["status"] != "accepted":
                self.send_json(200, {
                    "question": question,
                    "subject": subject_result["subject"],
                    "status": "skipped",
                    "reason": subject_result["reason"]
                })
                return

            result = analyse_question(question)

            if not isinstance(result, dict):
                result = {"analysis": result}

            result["subject"] = "Java"
            result["status"] = "analyzed"
            result["subject_reason"] = subject_result["reason"]

            self.send_json(200, result)

        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "Invalid JSON request"})
        except Exception as error:
            print("[ML API ERROR]", str(error))
            self.send_json(500, {
                "error": "Question analysis failed"
            })

    def log_message(self, format, *args):
        print("[ML API]", format % args)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 5000), MLRequestHandler)
    print("PaperMind AI ML API running at http://127.0.0.1:5000")
    print("Health: http://127.0.0.1:5000/health")
    print("Analysis: POST http://127.0.0.1:5000/analyze")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ML service...")
    finally:
        server.server_close()
