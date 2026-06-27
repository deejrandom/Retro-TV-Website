from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import json
import os

app = Flask(__name__)
CORS(app)

app.secret_key = "RetroTV_SecretKey_2026_StableBase"

ADMIN_PASSWORD = "MuffinBennett!987"
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
    return {"vhf": [], "uhf": []}

def save_schedule(data):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# LOGIN (Simple)
# =====================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body style="background:#0a0a1f; color:#39ff14; font-family:sans-serif; padding:40px; text-align:center;">
    <h1>Retro TV Admin</h1>
    <form method="post">
        <input type="password" name="password" placeholder="Password" style="padding:12px; width:300px;"><br><br>
        <button type="submit" style="padding:12px 30px;">Login</button>
    </form>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            login_user(User("admin"))
            return redirect('/admin')
        return "Invalid password", 401
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# =====================
# ADMIN (Basic for now)
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Admin</title></head>
<body style="background:#0a0a1f; color:#39ff14; padding:30px; font-family:sans-serif;">
    <h1>Retro TV Admin</h1>
    <p>Admin is working. Full features will be restored soon.</p>
    <a href="/logout">Logout</a>
</body>
</html>
"""

@app.route('/admin')
@login_required
def admin():
    return render_template_string(ADMIN_HTML)

# =====================
# API
# =====================
@app.route('/api/schedule')
def get_schedule():
    return jsonify(load_schedule())

@app.route('/api/schedule', methods=['POST'])
@login_required
def update_schedule():
    new_data = request.get_json()
    if not new_data:
        return jsonify({"error": "No data"}), 400
    save_schedule(new_data)
    return jsonify({"message": "Saved"})

if __name__ == '__main__':
    app.run(debug=True)