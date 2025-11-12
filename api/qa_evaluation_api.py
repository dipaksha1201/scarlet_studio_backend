import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import subprocess
import sys

QUIZ_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "quiz_output.json")
PERF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "performance.json")

# Try to import helpers from the CLI module. Support both package relative import
# (when run as part of package) and plain script import (when running file directly).
try:
    from .qa_evaluation import run_interactive_quiz, save_performance, load_quizzes
except Exception:
    # fallback when executed as a script (no package context)
    from qa_evaluation import run_interactive_quiz, save_performance, load_quizzes

# HTTP API server
class SimpleHandler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/performance":
            if not os.path.exists(PERF_PATH):
                self._send_json({"error": "performance.json not found"}, code=404)
                return
            try:
                with open(PERF_PATH, "r") as f:
                    content = json.load(f)
                self._send_json({"performance": content})
            except Exception as e:
                self._send_json({"error": f"failed to read performance: {e}"}, code=500)
            return
        # health
        if parsed.path == "/":
            self._send_json({"status": "ok"})
            return
        self._send_json({"error": "not found"}, code=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/run":
            # Attempt to run the interactive CLI attached to the local tty so user can answer in terminal.
            tty_path = "/dev/tty"
            # Prefer launching the stand-alone CLI script attached to the terminal so user can interact.
            if os.path.exists(tty_path):
                try:
                    with open(tty_path, "r+") as tty:
                        script = os.path.join(os.path.dirname(__file__), "qa_evaluation.py")
                        subprocess.run([sys.executable, script], stdin=tty, stdout=tty, stderr=tty)
                    self._send_json({"status": "interactive run completed (see terminal)"})
                except Exception as e:
                    self._send_json({"error": f"failed to run interactive CLI via subprocess: {e}"}, code=500)
                return
            # If no tty, attempt to call the function directly (may fail if stdin isn't available).
            try:
                run_interactive_quiz()
                self._send_json({"status": "interactive run invoked (no tty)"})
            except Exception as e:
                self._send_json({"error": f"no tty and failed to invoke CLI function: {e}"}, code=500)
            return

        if parsed.path == "/simulate":
            # read request body as JSON array of performance entries and append them
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else ""
            try:
                entries = json.loads(body)
                if not isinstance(entries, list):
                    raise ValueError("payload must be a JSON array of entries")
                # use save_performance imported from qa_evaluation
                save_performance(entries, path=PERF_PATH)
                self._send_json({"status": "saved", "count": len(entries)})
            except Exception as e:
                self._send_json({"error": f"failed to parse/save entries: {e}"}, code=400)
            return

        self._send_json({"error": "not found"}, code=404)

def run_server(host="127.0.0.1", port=8000):
    server = HTTPServer((host, port), SimpleHandler)
    print(f"API server listening at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.server_close()

if __name__ == "__main__":
    run_server()
