"""
app.py - Flask Web Application for CODSOFT Rule-Based Chatbot.

This module provides:
1. Web server and API routes for chat interaction.
2. Secure browser cookie-based session tracking.
3. Message history loading, saving, and clearing.
4. User memory retrieval and deletion endpoints.
5. Error handling and input validation.
"""

import os
import uuid
from typing import Any, Dict, Tuple
from flask import Flask, Response, jsonify, make_response, render_template, request

import chatbot
import database

# Initialize Flask application
app = Flask(__name__)
# Secret key for sessions
app.secret_key = os.environ.get("SECRET_KEY", "codsoft-chatbot-dev-secret-key-2026")

# Initialize SQLite database and tables upon server startup
database.init_db()


def resolve_session() -> Tuple[str, bool]:
    """
    Retrieve existing session_id from browser cookies or request header.
    If no session exists, generate a cryptographically random UUID.
    Returns (session_id, is_new_session).
    """
    # Check browser cookie first, then custom header fallback
    session_id = request.cookies.get("session_id") or request.headers.get("X-Session-ID")
    if session_id and len(session_id.strip()) >= 8:
        return session_id.strip(), False

    # Generate a new unpredictable session ID
    new_id = uuid.uuid4().hex
    return new_id, True


def attach_session_cookie(response: Response, session_id: str) -> Response:
    """
    Set a persistent session cookie in the HTTP response.
    Cookie lives for 30 days so memory & history persist across browser restarts.
    """
    response.set_cookie(
        "session_id",
        session_id,
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=False,  # Allow frontend JS to check session id if needed
        samesite="Lax",  # CSRF defense while allowing standard top-level navigation
    )
    return response


@app.route("/")
def index():
    """
    Render the main chatbot web interface.
    Attaches a persistent session cookie if one is not already present.
    """
    session_id, is_new = resolve_session()
    resp = make_response(render_template("index.html", session_id=session_id))
    if is_new:
        attach_session_cookie(resp, session_id)
    return resp


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    """
    Process incoming user chat message:
    1. Validates the JSON payload and message content.
    2. Saves the user message to SQLite.
    3. Executes rule-based reasoning in chatbot.py.
    4. Saves the bot's reply to SQLite.
    5. Returns both the bot reply and message metadata.
    """
    session_id, is_new = resolve_session()

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid request. Expected JSON object."}), 400

    raw_message = data.get("message", "")
    if not isinstance(raw_message, str) or not raw_message.strip():
        return jsonify({"status": "error", "message": "Message cannot be empty."}), 400

    cleaned_input = raw_message.strip()
    if len(cleaned_input) > 1000:
        return jsonify({"status": "error", "message": "Message is too long (maximum 1000 characters)."}), 400

    # 1. Save user message to database
    user_record = database.save_message(session_id, "user", cleaned_input)

    # 2. Generate response using rule-based engine
    bot_reply = chatbot.generate_response(session_id, cleaned_input)

    # 3. Save bot response to database
    bot_record = database.save_message(session_id, "bot", bot_reply)

    response_payload = {
        "status": "success",
        "session_id": session_id,
        "user_message": user_record,
        "bot_message": bot_record,
    }

    resp = make_response(jsonify(response_payload), 200)
    if is_new:
        attach_session_cookie(resp, session_id)
    return resp


@app.route("/api/history", methods=["GET"])
def history_endpoint():
    """
    Fetch all conversation messages for the current session.
    Allows restoring messages when refreshing or reopening the webpage.
    """
    session_id, is_new = resolve_session()
    messages = database.get_messages(session_id)
    resp = make_response(
        jsonify({
            "status": "success",
            "session_id": session_id,
            "count": len(messages),
            "history": messages,
        }),
        200,
    )
    if is_new:
        attach_session_cookie(resp, session_id)
    return resp


@app.route("/api/history/clear", methods=["POST"])
def clear_history_endpoint():
    """
    Clear all saved messages for the current session.
    Crucial: This preserves saved user memories (name, preferences) in user_memory table.
    """
    session_id, is_new = resolve_session()
    deleted_count = database.clear_messages(session_id)
    resp = make_response(
        jsonify({
            "status": "success",
            "session_id": session_id,
            "deleted_count": deleted_count,
            "message": "Chat history cleared successfully. Saved personal memories remain preserved.",
        }),
        200,
    )
    if is_new:
        attach_session_cookie(resp, session_id)
    return resp


@app.route("/api/memory", methods=["GET"])
def get_memory_endpoint():
    """
    Fetch all persistent memories saved for the current session.
    """
    session_id, is_new = resolve_session()
    memories = database.get_all_memories(session_id)
    resp = make_response(
        jsonify({
            "status": "success",
            "session_id": session_id,
            "memories": memories,
        }),
        200,
    )
    if is_new:
        attach_session_cookie(resp, session_id)
    return resp


@app.route("/api/memory/clear", methods=["POST"])
def clear_memory_endpoint():
    """
    Delete all stored memories for the current session.
    """
    session_id, is_new = resolve_session()
    deleted_count = database.clear_all_memories(session_id)
    resp = make_response(
        jsonify({
            "status": "success",
            "session_id": session_id,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} saved memor{'y' if deleted_count == 1 else 'ies'}.",
        }),
        200,
    )
    if is_new:
        attach_session_cookie(resp, session_id)
    return resp


@app.route("/api/memory/delete", methods=["POST"])
def delete_single_memory_endpoint():
    """
    Delete a specific memory key (e.g., 'name', 'favorite_color') for this session.
    """
    session_id, is_new = resolve_session()
    data = request.get_json(silent=True) or {}
    key = data.get("key", "").strip().lower()

    if not key:
        return jsonify({"status": "error", "message": "Memory key must be specified."}), 400

    deleted = database.delete_memory(session_id, key)
    resp = make_response(
        jsonify({
            "status": "success",
            "deleted": bool(deleted),
            "message": f"Memory key '{key}' deleted." if deleted else f"Key '{key}' was not found.",
        }),
        200,
    )
    if is_new:
        attach_session_cookie(resp, session_id)
    return resp


@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found errors with JSON."""
    return jsonify({"status": "error", "message": "Endpoint not found."}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 Internal Server errors gracefully."""
    return jsonify({"status": "error", "message": "An internal server error occurred."}), 500


if __name__ == "__main__":
    print("=" * 60)
    print(" Starting CODSOFT Rule-Based Chatbot...")
    print(" Access the application at: http://127.0.0.1:5000")
    print(" Press Ctrl+C to stop the server.")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
