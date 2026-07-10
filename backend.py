from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'retro-tv-secret-key-2026'

# =====================
# PASSWORD (Hardcoded for now)
# =====================
ADMIN_PASSWORD = "MuffinBennett!987"
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

SCHEDULE_FILE = 'schedule.json'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    <title>Admin Login - Retro TV</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 50px; text-align: center; }
        h1 { color: #ffcc00; }
        input { background: #111; color: #fff; border: 3px solid #556677; padding: 14px; font-size: 18px; width: 320px; margin: 15px 0; }
        button { background: #39ff14; color: #000; border: none; padding: 14px 40px; font-family: 'Press Start 2P', cursive; font-size: 16px; cursor: pointer; }
        button:hover { background: #ffcc00; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <form method="POST">
        <input type="password" name="password" placeholder="Enter Password" required><br>
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
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 30px; max-width: 900px; margin: 0 auto; }
        h1, h2 { color: #ffcc00; }
        .section { background: #111; border: 3px solid #334455; padding: 20px; margin-bottom: 25px; }
        pre { background: #1a1a1a; padding: 15px; overflow-x: auto; border: 2px solid #556677; }
        button { background: #39ff14; color: #000; border: none; padding: 10px 20px; font-family: 'Press Start 2P', cursive; cursor: pointer; }
        button:hover { background: #ffcc00; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <p><a href="/logout" style="color:#ffcc00;">Logout</a></p>

    <div class="section">
        <h2>Current Schedule Data</h2>
        <pre id="scheduleData"></pre>
        <button onclick="refreshData()">Refresh Data</button>
    </div>

    <div class="section">
        <h2>Quick Actions</h2>
        <p>You can also use the full admin tools later. For now, you can manually edit <code>schedule.json</code> on Render if needed.</p>
    </div>

    <script>
        async function refreshData() {
            const res = await fetch('/api/schedule');
            const data = await res.json();
            document.getElementById('scheduleData').textContent = JSON.stringify(data, null, 2);
        }
        refreshData();
    </script>
</body>
</html>
"""

# =====================
# ROUTES
# =====================

@app.route('/api/schedule')
def get_schedule():
    return jsonify(load_schedule())

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
def admin():
    return render_template_string(ADMIN_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)