import os
from flask import Flask, jsonify

app = Flask(__name__)
VERSION = os.getenv("APP_VERSION", "dev")
COLOR = os.getenv("APP_COLOR", "none")
BREAK = os.getenv("BREAK", "false") == "true"

@app.route("/")
def home():
    return f"Hello from {COLOR} v{VERSION}\n"

@app.route("/health")
def health():
    if BREAK:
        return jsonify(status="DOWN"), 500
    return jsonify(status="UP", color=COLOR, version=VERSION)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
