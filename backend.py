from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)
CORS(app)

# =====================
# SECRET KEY (Required)
# =====================
app.secret_key = "RetroTV_SecretKey_2026_FinalFix_987654"

# =====================
# CONFIG
# =====================
ADMIN_PASSWORD = "MuffinBennett!987"          # ← Your password
SCHEDULE_FILE = 'schedule.json'

app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
# LOGIN PAGE (Simple Password Only)
# =====================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Retro TV - Login</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
        body { background: linear-gradient(135deg, #0a0a1f 0%, #1a0033 100%); color: #39ff14; font-family: 'Press Start 2P', cursive; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .login-box { background: #111; border: 6px solid #334455; padding: 40px; width: 420px; box-shadow: 0 0 30px rgba(57, 255, 20, 0.3); }
        h1 { color: #ffcc00; text-align: center; margin-bottom: 30px; font-size: 22px; }
        input { width: 100%; padding: 14px; margin: 10px 0; background: #222; border: 3px solid #556677; color: #fff; font-family: 'Press Start 2P', cursive; font-size: 14px; }
        button { width: 100%; padding: 16px; background: #39ff14; color: #000; border: none; font-family: 'Press Start 2P', cursive; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; }
        button:hover { background: #ffcc00; }
        .error { color: #ff4444; text-align: center; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>RETRO TV</h1>
        <form method="post">
            <input type="password" name="password" placeholder="ENTER PASSWORD" required>
            <button type="submit">LOGIN</button>
        </form>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
    </div>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            login_user(User("admin"))
            return redirect('/admin')
        error = "Invalid password"
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# =====================
# ADMIN PAGE (Your full working version)
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Retro TV Admin</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 30px; max-width: 1100px; margin: 0 auto; }
        h1, h2 { color: #ffcc00; }
        .section { background: #111; border: 3px solid #334455; padding: 20px; margin-bottom: 30px; }
        input, select, button, textarea { background: #222; color: #fff; border: 2px solid #555; padding: 8px; margin: 6px 0; font-family: inherit; width: 100%; box-sizing: border-box; }
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 8px 16px; }
        button:hover { background: #ffcc00; }
        .media-item { background: #1a1a1a; border: 2px solid #444; padding: 15px; margin: 12px 0; }
        .add-form, .edit-form { background: #1f2a1f; border: 2px solid #39ff14; padding: 15px; margin-top: 12px; display: none; }
        .add-form.active, .edit-form.active { display: block; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <a href="/logout" style="color:#ffcc00;">Logout</a>

    <div class="section">
        <h2>Add New Channel</h2>
        <select id="newBand"><option value="vhf">VHF</option><option value="uhf">UHF</option></select>
        <input type="text" id="newChannelName" placeholder="Channel Name">
        <input type="text" id="newChannelSchedule" placeholder="Schedule text">
        <select id="newPresentation">
            <option value="single">Single</option>
            <option value="gallery">Gallery</option>
            <option value="linkcards">Link Cards</option>
        </select>
        <button onclick="addChannel()">Add Channel</button>
    </div>

    <div class="section">
        <h2>Manage Channels</h2>
        <div id="channelList"></div>
    </div>

    <!-- GUIDE SCROLL SPEED - AT THE BOTTOM -->
    <div class="section">
        <h2>Guide Scroll Speed</h2>
        <input type="number" id="scrollSpeed" step="0.05" value="0.36">
        <button onclick="saveScrollSpeed()">Save Speed</button>
        <p style="color:#aaa; font-size:12px;">Lower = slower crawl. Recommended: 0.20 – 0.80</p>
    </div>

    <script>
        // ==================== YOUR FULL ADMIN JAVASCRIPT ====================
        let scheduleData = {};

        async function loadSchedule() {
            const res = await fetch('/api/schedule');
            scheduleData = await res.json();
            renderChannels();
        }

        function renderChannels() {
            const container = document.getElementById('channelList');
            container.innerHTML = '';

            ['vhf', 'uhf'].forEach(band => {
                (scheduleData[band] || []).forEach((ch, index) => {
                    const div = document.createElement('div');
                    div.className = 'media-item';
                    div.innerHTML = `
                        <strong>${band.toUpperCase()} ${index + 2} • ${ch.name}</strong><br>
                        Presentation: <strong>${ch.presentation || 'single'}</strong><br><br>
                        <button onclick="editChannel('${band}', ${index})">Edit Channel</button>
                        <button onclick="deleteChannel('${band}', ${index})" style="background:#ff4444; color:white;">Delete</button>

                        <div style="margin-top:15px;">
                            <h4 style="color:#ffcc00;">Media Items</h4>
                            <div id="media-list-${band}-${index}"></div>
                            <button onclick="showAddMediaForm('${band}', ${index}, this)">+ Add Media</button>
                            <div id="add-form-${band}-${index}" class="add-form"></div>
                        </div>
                    `;
                    container.appendChild(div);
                    renderMediaList(band, index);
                });
            });
        }

        // ... (rest of your JavaScript from previous working version) ...
        // Paste the rest of your admin JS functions here if they are missing
    </script>
</body>
</html>
"""

@app.route('/admin')
@login_required
def admin():
    return render_template_string(ADMIN_HTML)

if __name__ == '__main__':
    app.run(debug=True, port=5000)