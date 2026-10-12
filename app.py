"""
DSA Tutor Chatbot - Backend
---------------------------
A small Flask API that sits between the browser frontend and Google's
Gemini API. The API key lives ONLY here (in an environment variable),
never in the browser, so it can't be stolen from page source or dev tools.

Gemini has a genuinely free, no-credit-card tier for Flash-class models,
which is why this project defaults to it.

Run:
    pip install -r requirements.txt
    export GEMINI_API_KEY=...      (Windows cmd: set GEMINI_API_KEY=...)
    python app.py
Then open http://localhost:5000 in your browser.
"""

import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types
from google.genai.errors import APIError

load_dotenv()  # reads the .env file in this folder and loads it into the environment

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)  # allow the frontend to call this API during local dev

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("GEMINI_API_KEY")
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash")
ALLOWED_MODELS = {"gemini-3.1-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"}

SYSTEM_PROMPT = """You are "DSA Tutor", a friendly and patient Data Structures &
Algorithms teaching assistant for students preparing for coding interviews
and CS coursework.

Teaching style rules:
1. Understand first: briefly restate the problem in your own words so the
   student knows you understood it correctly.
2. Guide, don't just solve: start with a hint or the key idea/pattern
   (e.g. "this is a sliding window problem") before jumping to full code.
   If the student explicitly asks for the full solution, give it.
3. Explain the "why": walk through the intuition, not just the steps.
4. Complexity: always state time and space complexity, and briefly explain why.
5. Edge cases: point out common edge cases and pitfalls.
6. Code: when you give code, keep it clean, commented, and in the language
   the student asks for (default to Python if unspecified).
7. Be encouraging and concise. Use short paragraphs, bullet points, and
   numbered steps rather than huge walls of text.
8. If a question is not related to DSA/programming/CS fundamentals, gently
   steer the conversation back to DSA topics.
"""

client = genai.Client(api_key=API_KEY) if API_KEY else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Serve the frontend."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "key_configured": bool(API_KEY)})


@app.route("/api/chat", methods=["POST"])
def chat():
    if not client:
        return jsonify({
            "error": "Server has no GEMINI_API_KEY configured. "
                     "Set it as an environment variable and restart the server."
        }), 500

    body = request.get_json(silent=True) or {}
    messages = body.get("messages")  # [{role: "user"/"assistant", content}, ...]
    model = body.get("model", DEFAULT_MODEL)

    if not messages or not isinstance(messages, list):
        return jsonify({"error": "Request must include a non-empty 'messages' list."}), 400

    if model not in ALLOWED_MODELS:
        model = DEFAULT_MODEL

    # keep only the last 20 turns so requests don't grow unbounded
    messages = messages[-20:]

    # Gemini expects roles "user" and "model" (not "assistant"), and each
    # message as {role, parts: [{text}]}.
    contents = [
        {
            "role": "model" if m["role"] == "assistant" else "user",
            "parts": [{"text": m["content"]}],
        }
        for m in messages
    ]

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=1200,
            ),
        )
        return jsonify({"reply": response.text})

    except APIError as e:
        return jsonify({"error": f"Gemini API error ({e.code}): {e.message}"}), 502
    except Exception as e:  # noqa: BLE001 - surface unexpected errors to the client
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
