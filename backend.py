from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'retro-tv-secret-key-2026'

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
    <title>Admin Login</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 60px; text-align: center; }
        input { background: #111; color: #fff; border: 3px solid #556677; padding: 14px; font-size: 18px; width: 320px; }
        button { background: #39ff14; color: #000; border: none; padding: 14px 40px; font-family: 'Press Start 2P', cursive; font-size: 16px; cursor: pointer; }
        button:hover { background: #ffcc00; }
    </style>
</head>
<body>
    <h1 style="color:#ffcc00;">Retro TV Admin</h1>
    <form method="POST">
        <input type="password" name="password" placeholder="Password" required><br><br>
        <button type="submit">Login</button>
    </form>
</body>
</html>
"""

# =====================
# FULL ADMIN PAGE
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Retro TV</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 20px; max-width: 1300px; margin: 0 auto; }
        h1, h2, h3 { color: #ffcc00; }
        .section { background: #111; border: 3px solid #334455; padding: 20px; margin-bottom: 25px; }
        input, select, button, textarea { background: #222; color: #fff; border: 2px solid #555; padding: 8px; margin: 5px 0; width: 100%; box-sizing: border-box; font-family: inherit; }
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 10px 18px; }
        button:hover { background: #ffcc00; }
        .channel-card { background: #1a1a1a; border: 2px solid #556677; padding: 15px; margin-bottom: 20px; }
        .media-item { background: #222; border: 1px solid #555; padding: 10px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; }
        .form-row { display: flex; gap: 10px; }
        .form-row > * { flex: 1; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <p><a href="/logout" style="color:#ffcc00;">Logout</a></p>

    <!-- Add Channel -->
    <div class="section">
        <h2>Add New Channel</h2>
        <form id="addChannelForm">
            <div class="form-row">
                <select name="band">
                    <option value="vhf">VHF</option>
                    <option value="uhf">UHF</option>
                </select>
                <input type="text" name="name" placeholder="Channel Name" required>
            </div>
            <input type="text" name="schedule" placeholder="Schedule Description">
            <select name="presentation">
                <option value="single">Single Content</option>
                <option value="gallery">Gallery</option>
                <option value="linkcards">Linkcards</option>
            </select>
            <button type="submit">Add Channel</button>
        </form>
    </div>

    <!-- Existing Channels -->
    <div class="section">
        <h2>Existing Channels</h2>
        <div id="channelList"></div>
    </div>

    <script>
        let scheduleData = {};

        async function loadData() {
            const res = await fetch('/api/schedule');
            scheduleData = await res.json();
            renderChannels();
        }

        function renderChannels() {
            const container = document.getElementById('channelList');
            container.innerHTML = '';

            ['vhf', 'uhf'].forEach(band => {
                scheduleData[band].forEach((ch, index) => {
                    const div = document.createElement('div');
                    div.className = 'channel-card';

                    let mediaHTML = '';
                    if (ch.media && ch.media.length > 0) {
                        mediaHTML = '<h3>Media</h3>';
                        ch.media.forEach((m, mIndex) => {
                            mediaHTML += `
                                <div class="media-item">
                                    <span>${m.title || m.type} (${m.type})</span>
                                    <button onclick="deleteMedia('${band}', ${index}, ${mIndex})">Delete</button>
                                </div>`;
                        });
                    }

                    div.innerHTML = `
                        <h3>${band.toUpperCase()} - ${ch.name}</h3>
                        
                        <label>Channel Name</label>
                        <input type="text" id="name-${band}-${index}" value="${ch.name}">
                        
                        <label>Schedule</label>
                        <input type="text" id="schedule-${band}-${index}" value="${ch.schedule || ''}">
                        
                        <label>Presentation Style</label>
                        <select id="presentation-${band}-${index}">
                            <option value="single" ${ch.presentation === 'single' ? 'selected' : ''}>Single</option>
                            <option value="gallery" ${ch.presentation === 'gallery' ? 'selected' : ''}>Gallery</option>
                            <option value="linkcards" ${ch.presentation === 'linkcards' ? 'selected' : ''}>Linkcards</option>
                        </select>

                        <br><br>
                        <button onclick="saveChannel('${band}', ${index})">Save Changes</button>
                        <button onclick="deleteChannel('${band}', ${index})">Delete Channel</button>

                        <br><br>
                        <h3>Add Media</h3>
                        <select id="mediaType-${band}-${index}">
                            <option value="image">Image</option>
                            <option value="youtube">YouTube Video</option>
                            <option value="text">Text</option>
                            <option value="linkcard">Linkcard</option>
                        </select>
                        <input type="text" id="mediaTitle-${band}-${index}" placeholder="Title">
                        <input type="text" id="mediaUrl-${band}-${index}" placeholder="URL or content">
                        <button onclick="addMedia('${band}', ${index})">Add Media</button>

                        ${mediaHTML}
                    `;
                    container.appendChild(div);
                });
            });
        }

        async function saveChannel(band, index) {
            const ch = scheduleData[band][index];
            ch.name = document.getElementById(`name-${band}-${index}`).value;
            ch.schedule = document.getElementById(`schedule-${band}-${index}`).value;
            ch.presentation = document.getElementById(`presentation-${band}-${index}`).value;

            await saveData();
            alert("Channel updated!");
            loadData();
        }

        async function deleteChannel(band, index) {
            if (!confirm("Delete this channel?")) return;
            scheduleData[band].splice(index, 1);
            await saveData();
            loadData();
        }

        async function addMedia(band, index) {
            const ch = scheduleData[band][index];
            if (!ch.media) ch.media = [];

            const type = document.getElementById(`mediaType-${band}-${index}`).value;
            const title = document.getElementById(`mediaTitle-${band}-${index}`).value;
            const url = document.getElementById(`mediaUrl-${band}-${index}`).value;

            ch.media.push({ type, title, url });
            await saveData();
            loadData();
        }

        async function deleteMedia(band, chIndex, mediaIndex) {
            if (!confirm("Delete this media item?")) return;
            scheduleData[band][chIndex].media.splice(mediaIndex, 1);
            await saveData();
            loadData();
        }

        async function saveData() {
            await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scheduleData)
            });
        }

        // Add new channel
        document.getElementById('addChannelForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const form = new FormData(this);
            const newChannel = {
                id: form.get('name').toLowerCase().replace(/\s+/g, '-'),
                name: form.get('name'),
                schedule: form.get('schedule'),
                presentation: form.get('presentation'),
                media: []
            };
            scheduleData[form.get('band')].push(newChannel);
            await saveData();
            this.reset();
            loadData();
        });

        loadData();
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
    return jsonify({"message": "Saved successfully"})

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