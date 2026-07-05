import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DATA_FILE = "cosmetics_data.json"

VALID_SLOTS = {
    "CAPE",
    "HAT",
    "WINGS",
    "TRAIL",
    "PARTICLES"
}


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


cosmetics_data = load_data()


class CosmeticsHandler(BaseHTTPRequestHandler):

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        # GET /health
        if parsed.path == "/health":
            self.send_json({
                "status": "ok",
                "players": len(cosmetics_data)
            })
            return

        # GET /cosmetics/batch?ids=uuid1,uuid2,...
        if parsed.path == "/cosmetics/batch":
            query = parse_qs(parsed.query)

            ids = query.get("ids", [""])[0].split(",")

            result = {}

            for uuid in ids:
                uuid = uuid.strip()
                if uuid and uuid in cosmetics_data:
                    result[uuid] = cosmetics_data[uuid]

            self.send_json(result)
            return

        self.send_json({"error": "Not Found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        # POST /cosmetics/<uuid>
        if parsed.path.startswith("/cosmetics/"):

            uuid = parsed.path[len("/cosmetics/"):]

            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            try:
                received = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
                return

            filtered = {}

            for slot, cosmetic in received.items():
                if slot in VALID_SLOTS:
                    filtered[slot] = cosmetic

            cosmetics_data[uuid] = filtered
            save_data(cosmetics_data)

            self.send_json({"success": True})
            return

        self.send_json({"error": "Not Found"}, 404)


def main():
    port = int(os.environ.get("PORT", 8080))

    server = HTTPServer(("0.0.0.0", port), CosmeticsHandler)

    print(f"Cosmetics server in ascolto sulla porta {port}")

    server.serve_forever()


if __name__ == "__main__":
    main()
