from flask import Flask, jsonify, request, render_template_string, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import json
import os

app = Flask(__name__)
CORS(app)

# =====================
# SECRET KEY (Required)
# =====================
app.secret_key = "RetroTV_SecretKey_2026_FinalFix_XYZ789"

# =====================
# CONFIG
# =====================
ADMIN_PASSWORD = "MuffinBennett!987"   # ← Your password
SCHEDULE_FILE = "schedule.json"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {"vhf": [], "uhf": [], "guide_scroll_speed": 0.36}

def save_schedule(data):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# LOGIN PAGE
# =====================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Retro TV</title>
    <style>
        body { background: #0a0a1f; color: #39ff14; font-family: 'Press Start 2P', system-ui; padding: 40px; text-align: center; }
        input { padding: 12px; font-size: 18px; width: 300px; margin: 10px; background: #111; color: white; border: 3px solid #556677; }
        button { padding: 12px 30px; font-size: 18px; background: #39ff14; color: black; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <form method="POST">
        <input type="password" name="password" placeholder="Enter Admin Password" required><br>
        <button type="submit">Login</button>
    </form>
</body>
</html>
"""

# =====================
# ADMIN PAGE (Basic but working)
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Retro TV</title>
    <style>
        body { background: #0a0a1f; color: #39ff14; font-family: 'Press Start 2P', system-ui; padding: 30px; }
        h1 { color: #ffcc00; }
        a { color: #ffcc00; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <p style="color:#ffcc00;">✅ Login successful!</p>
    <p>You can now access the admin functions.</p>
    <p><a href="/api/schedule" target="_blank">View Current Schedule Data</a></p>
    <br>
    <a href="/logout">Logout</a>
</body>
</html>
"""

# =====================
# ROUTES
# =====================

@app.route('/')
def home():
    return "Retro TV Backend is running."

@app.route('/api/schedule')
def get_schedule():
    data = load_schedule()
    return jsonify(data)

@app.route('/api/schedule', methods=['POST'])
@login_required
def update_schedule():
    new_data = request.get_json()
    if not new_data:
        return jsonify({"error": "No data provided"}), 400
    save_schedule(new_data)
    return jsonify({"message": "Schedule updated successfully"})

@app.route('/admin')
@login_required
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            user = User("admin")
            login_user(user)
            return redirect('/admin')
        return "Invalid password", 401
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# =====================
# RUN
# =====================
if __name__ == '__main__':
    app.run(debug=True)