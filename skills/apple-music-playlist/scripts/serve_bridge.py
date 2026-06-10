"""One-shot local server for capturing the Music User Token (MUT).

Usage: ~/.claude/skills-venv/bin/python serve_bridge.py
Then open http://localhost:8765 in Safari (handles Apple ID auth most reliably).
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # allow run from any cwd

from auth import generate_developer_token, load_credentials, CRED_PATH

PORT = 8765
BRIDGE_HTML = Path(__file__).resolve().parent / "musickit_bridge.html"


class Handler(BaseHTTPRequestHandler):
    creds = None
    dev_token = None

    def do_GET(self):
        if self.path == "/":
            html = BRIDGE_HTML.read_text().replace(
                '<meta charset="utf-8">',
                f'<meta charset="utf-8">'
                f'<meta name="dev-token" content="{self.dev_token}">',
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/save-token":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            self.creds["music_user_token"] = body["music_user_token"]
            with CRED_PATH.open("w") as f:
                json.dump(self.creds, f, indent=2)
            CRED_PATH.chmod(0o600)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            print(f"Saved MUT to {CRED_PATH}")
        else:
            self.send_response(404)
            self.end_headers()


def main():
    creds = load_credentials()
    Handler.creds = creds
    Handler.dev_token = generate_developer_token(creds)
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"Open http://localhost:{PORT} in Safari to authorize.")
    server.serve_forever()


if __name__ == "__main__":
    main()
