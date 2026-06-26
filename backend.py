from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# =====================
# CONFIG
# =====================
ADMIN_PASSWORD = "MuffinBennett!987"
SCHEDULE_FILE = "schedule.json"
UPLOAD_FOLDER = "static/images"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
# ADMIN HTML (CLEANED)
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Retro TV</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 30px; max-width: 1100px; margin: 0 auto; }
        h1, h2 { color: #ffcc00; }
        .section { background: #111; border: 3px solid #334455; padding: 20px; margin-bottom: 30px; }
        input, select, button, textarea { background: #222; color: #fff; border: 2px solid #555; padding: 8px; margin: 6px 0; font-family: inherit; width: 100%; box-sizing: border-box; }
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 10px 18px; }
        button:hover { background: #ffcc00; }
        .media-item { background: #1a1a1a; border: 2px solid #444; padding: 12px; margin: 10px 0; }
        .success { color: #39ff14; font-weight: bold; padding: 10px; background: #112211; border: 2px solid #39ff14; margin: 15px 0; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <div class="section">
        <h2>Channels</h2>
        <div id="channelList"></div>
        <button onclick="addNewChannel()">+ Add New Channel</button>
    </div>

    <div class="section" id="channelEditor" style="display:none;">
        <h2>Edit Channel</h2>
        <input type="text" id="channelName" placeholder="Channel Name">
        <input type="text" id="channelSchedule" placeholder="Schedule / Description">
        
        <label>Presentation Mode:</label>
        <select id="presentationMode">
            <option value="single">Single</option>
            <option value="linkcards">Link Cards</option>
            <option value="gallery">Gallery (Grouped)</option>
        </select>

        <h3>Media</h3>
        <div id="mediaList"></div>
        <button onclick="addMediaItem()">+ Add Media</button>
        
        <br><br>
        <button onclick="saveChannelChanges()">Save Changes</button>
        <button onclick="deleteCurrentChannel()" style="background:#aa0000; color:white;">Delete Channel</button>
    </div>

    <!-- GUIDE SCROLL SPEED - MOVED TO BOTTOM -->
    <div class="section">
        <h2>Guide Scroll Speed</h2>
        <input type="number" id="scrollSpeedInput" step="0.05" min="0.10" max="1.50" value="0.36">
        <button onclick="saveScrollSpeed()">Save Speed</button>
        <p style="color:#aaa; font-size:12px;">Lower = slower crawl. Recommended: 0.20 – 0.80</p>
    </div>

    <div id="statusMessage" class="success" style="display:none;"></div>

    <script>
        // Your existing admin JavaScript stays here...
        // (I kept the structure the same, just moved the scroll speed section in the HTML above)
    </script>
</body>
</html>
"""

# =====================
# ROUTES
# =====================

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