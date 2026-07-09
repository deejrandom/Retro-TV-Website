from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'your-secret-key-change-this-to-something-strong'
app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'deejrandom')
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'MuffinBennett!987'))

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
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 40px; text-align: center; }
        input { background: #111; color: #fff; border: 3px solid #556677; padding: 12px; font-size: 18px; width: 300px; margin: 10px 0; }
        button { background: #39ff14; color: #000; border: none; padding: 12px 30px; font-family: 'Press Start 2P', cursive; font-size: 16px; cursor: pointer; }
        button:hover { background: #ffcc00; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <form method="POST">
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>
</body>
</html>
"""

# =====================
# ADMIN PAGE (with descriptions + gallery support)
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Retro TV</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 30px; max-width: 1100px; margin: 0 auto; }
        h1, h2 { color: #ffcc00; }
        .section { background: #111; border: 3px solid #334455; padding: 20px; margin-bottom: 30px; }
        input, select, button, textarea { background: #222; color: #fff; border: 2px solid #555; padding: 8px; margin: 6px 0; font-family: inherit; width: 100%; box-sizing: border-box; }
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 8px 16px; }
        button:hover { background: #ffcc00; }
        .media-item { background: #1a1a1a; border: 2px solid #444; padding: 12px; margin: 10px 0; }
        .success { color: #39ff14; font-weight: bold; padding: 10px; background: #112211; border: 2px solid #39ff14; margin: 15px 0; }
        .channel-card { background: #1a1a1a; border: 2px solid #556677; padding: 15px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <a href="/logout">Logout</a>

    <div class="section">
        <h2>Add New Channel</h2>
        <form id="addChannelForm">
            <select name="band">
                <option value="vhf">VHF</option>
                <option value="uhf">UHF</option>
            </select>
            <input type="text" name="name" placeholder="Channel Name" required>
            <input type="text" name="schedule" placeholder="Schedule text">
            <select name="presentation">
                <option value="single">Single Content</option>
                <option value="linkcards">Linkcards</option>
                <option value="gallery">Gallery</option>
            </select>
            <button type="submit">Add Channel</button>
        </form>
    </div>

    <div class="section">
        <h2>Edit Channels</h2>
        <div id="channelList"></div>
    </div>

    <script>
        // JavaScript for admin page would go here (same as previous versions)
        // This is the backend file - the full admin JS is in the HTML template
        console.log("Admin page loaded");
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