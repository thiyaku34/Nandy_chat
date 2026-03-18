import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
import datetime

# ---------------- APP SETUP ----------------
app = Flask(__name__, template_folder="../frontend")
app.config['SECRET_KEY'] = 'supersecretkey'

# ---------------- EXTENSIONS ----------------
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- USERS ----------------
users = {
    "admin": bcrypt.generate_password_hash("admin123").decode('utf-8'),
    "user": bcrypt.generate_password_hash("user123").decode('utf-8')
}

# ---------------- STATUS ----------------
online_users = {}

# ---------------- MESSAGES STORE ----------------
messages_db = {}

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and bcrypt.check_password_hash(users[username], password):
            session["user"] = username
            return redirect("/chat")
        else:
            return "❌ Invalid login"

    return render_template("login.html")


# ---------------- CHAT PAGE ----------------
@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html", user=session["user"])


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    user = session.get("user")
    if user:
        online_users[user] = "last seen " + datetime.datetime.now().strftime("%H:%M")
    session.clear()
    return redirect("/")


# ---------------- SOCKET EVENTS ----------------

# JOIN
@socketio.on("join")
def handle_join(data):
    user = data["user"]
    online_users[user] = "online"
    emit("update_status", online_users, broadcast=True)


# DISCONNECT
@socketio.on("disconnect")
def handle_disconnect():
    for user in online_users:
        online_users[user] = "last seen " + datetime.datetime.now().strftime("%H:%M")
    emit("update_status", online_users, broadcast=True)


# SEND MESSAGE
@socketio.on("send_message")
def handle_message(data):

    msg_id = data.get("id", str(datetime.datetime.now().timestamp()))

    message_data = {
        "id": msg_id,
        "user": data["user"],
        "message": data["message"],
        "time": data["time"],
        "seen": False,
        "reaction": ""
    }

    messages_db[msg_id] = message_data

    emit("receive_message", message_data, broadcast=True)


# TYPING
@socketio.on("typing")
def typing(data):
    emit("show_typing", data, broadcast=True)


# SEEN ✔✔
@socketio.on("seen")
def seen(data):
    msg_id = data["id"]

    if msg_id in messages_db:
        messages_db[msg_id]["seen"] = True

    emit("seen_update", {"id": msg_id}, broadcast=True)


# REACTION ❤️🔥😂
@socketio.on("react")
def react(data):
    msg_id = data["id"]
    emoji = data["emoji"]

    if msg_id in messages_db:
        messages_db[msg_id]["reaction"] = emoji

    emit("reaction_update", {
        "id": msg_id,
        "emoji": emoji
    }, broadcast=True)


# ---------------- CALL SIGNALING ----------------

@socketio.on("call_user")
def call_user(data):
    emit("incoming_call", data, broadcast=True)

@socketio.on("answer_call")
def answer_call(data):
    emit("call_answered", data, broadcast=True)

@socketio.on("ice_candidate")
def ice_candidate(data):
    emit("ice_candidate", data, broadcast=True)


# ---------------- RUN ----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)