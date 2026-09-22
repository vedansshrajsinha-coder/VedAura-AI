from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    jsonify
)

from werkzeug.security import generate_password_hash, check_password_hash
import os

from app.database import (
    create_tables,
    create_user,
    get_user_by_email,
    create_conversation,
    get_conversations,
    get_conversation,
    update_conversation,
    delete_conversation,
    delete_all_conversations
)

from app.engine import process_message

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

create_tables()

@app.route("/")
def home():
    return render_template(
        "index.html",
        logged_in=("user_id" in session),
        username=session.get("username")
    )

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    user = get_user_by_email(email)

    if not user:
        return "Email not found."

    if check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["email"] = user["email"]
        session.pop("guest_brain_history", None)
        return redirect("/")

    return "Incorrect password."

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return "Not logged in."

    return f"""
    User ID: {session['user_id']}<br>
    Username: {session['username']}<br>
    Email: {session['email']}
    """

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    if get_user_by_email(email):
        return "Email already exists."

    password_hash = generate_password_hash(password)
    create_user(username, email, password_hash)

    user = get_user_by_email(email)

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["email"] = user["email"]

    return redirect("/")

# ==========================================
# CONVERSATION API
# ==========================================

@app.route("/api/conversations", methods=["GET"])
def api_get_conversations():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in."}), 401

    return jsonify(get_conversations(session["user_id"]))

@app.route("/api/conversations", methods=["POST"])
def api_create_conversation():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in."}), 401

    data = request.get_json(silent=True) or {}
    title = data.get("title", "New Chat")

    conversation_id = create_conversation(
        session["user_id"],
        title
    )

    return jsonify({
        "success": True,
        "id": conversation_id,
        "title": title
    }), 201

@app.route("/api/conversations/<int:conversation_id>", methods=["GET"])
def api_get_conversation(conversation_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in."}), 401

    conversation = get_conversation(
        conversation_id,
        session["user_id"]
    )

    if not conversation:
        return jsonify({"error": "Conversation not found."}), 404

    return jsonify(conversation)

@app.route("/api/conversations/<int:conversation_id>", methods=["PUT"])
def api_update_conversation(conversation_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in."}), 401

    data = request.get_json(silent=True) or {}

    title = data.get("title", "New Chat")
    messages = data.get("messages", [])

    conversation = get_conversation(
        conversation_id,
        session["user_id"]
    )

    if not conversation:
        return jsonify({"error": "Conversation not found."}), 404

    update_conversation(
        conversation_id,
        session["user_id"],
        title,
        messages
    )

    return jsonify({"success": True})

@app.route("/api/conversations/<int:conversation_id>", methods=["DELETE"])
def api_delete_conversation(conversation_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in."}), 401

    conversation = get_conversation(
        conversation_id,
        session["user_id"]
    )

    if not conversation:
        return jsonify({"error": "Conversation not found."}), 404

    delete_conversation(
        conversation_id,
        session["user_id"]
    )

    return jsonify({"success": True})

@app.route("/api/conversations/clear", methods=["DELETE"])
def api_clear_conversations():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in."}), 401

    delete_all_conversations(session["user_id"])
    session.pop("guest_brain_history", None)

    return jsonify({"success": True})

def _conversation_history_for_request(message):
    """
    Recover the current chat's saved turns without changing the existing
    frontend API contract. The UI saves the user message immediately before
    calling /chat, so the latest matching conversation identifies the active chat.
    """
    if "user_id" not in session:
        return session.get("guest_brain_history", [])[-12:]

    conversations = get_conversations(session["user_id"])

    for conversation in conversations:
        messages = conversation.get("messages") or []

        if (
            messages
            and messages[-1].get("role") == "user"
            and messages[-1].get("text") == message
        ):
            return messages[-12:]

    return []

@app.route("/chat", methods=["POST"])
def chat():
    message = request.form["message"]
    uploaded_files = request.files.getlist("files")

    history = _conversation_history_for_request(message)

    # The current user message is passed separately to the brain.
    if (
        history
        and history[-1].get("role") == "user"
        and history[-1].get("text") == message
    ):
        history = history[:-1]

    try:
        reply = process_message(
            message,
            uploaded_files,
            conversation_history=history
        )
    except Exception as exc:
        app.logger.exception("AI Brain request failed")
        return jsonify({
            "error": f"AI Brain request failed: {exc}"
        }), 500

    # Guest users do not have a database conversation, so keep a small
    # server-side conversation history in the signed Flask session.
    if "user_id" not in session:
        guest_history = session.get("guest_brain_history", [])
        guest_history.extend([
            {"role": "user", "text": message},
            {"role": "assistant", "text": reply}
        ])
        session["guest_brain_history"] = guest_history[-12:]

    return reply

if __name__ == "__main__":
    app.run(debug=True)
