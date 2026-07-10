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
# DROPDOWN STYLE ADMIN PAGE
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Retro TV</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 25px; max-width: 1100px; margin: 0 auto; }
        h1, h2, h3 { color: #ffcc00; }
        .section { background: #111; border: 3px solid #334455; padding: 20px; margin-bottom: 25px; }
        select, input, button, textarea { background: #222; color: #fff; border: 2px solid #555; padding: 10px; margin: 8px 0; width: 100%; box-sizing: border-box; font-family: inherit; }
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 12px 24px; }
        button:hover { background: #ffcc00; }
        .media-item { background: #1a1a1a; border: 1px solid #555; padding: 10px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; }
        #editForm { display: none; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <p><a href="/logout" style="color:#ffcc00;">Logout</a></p>

    <!-- Add New Channel -->
    <div class="section">
        <h2>Add New Channel</h2>
        <form id="addChannelForm">
            <select name="band">
                <option value="vhf">VHF</option>
                <option value="uhf">UHF</option>
            </select>
            <input type="text" name="name" placeholder="Channel Name" required>
            <input type="text" name="schedule" placeholder="Schedule Description">
            <select name="presentation">
                <option value="single">Single Content</option>
                <option value="gallery">Gallery</option>
                <option value="linkcards">Linkcards</option>
            </select>
            <button type="submit">Add Channel</button>
        </form>
    </div>

    <!-- Edit Existing Channel -->
    <div class="section">
        <h2>Edit Channel</h2>
        
        <label><strong>Select Channel to Edit:</strong></label>
        <select id="channelSelect" onchange="loadSelectedChannel()">
            <option value="">-- Select a Channel --</option>
        </select>

        <div id="editForm">
            <h3 id="editingTitle"></h3>

            <label>Channel Name</label>
            <input type="text" id="editName">

            <label>Schedule Description</label>
            <input type="text" id="editSchedule">

            <label>Presentation Style</label>
            <select id="editPresentation">
                <option value="single">Single Content</option>
                <option value="gallery">Gallery</option>
                <option value="linkcards">Linkcards</option>
            </select>

            <br><br>
            <button onclick="saveChannelChanges()">Save Changes</button>
            <button onclick="deleteSelectedChannel()" style="background:#cc4444; color:white;">Delete Channel</button>

            <br><br>
            <h3>Add Media</h3>
            <select id="mediaType">
                <option value="image">Image</option>
                <option value="youtube">YouTube Video</option>
                <option value="text">Text</option>
                <option value="linkcard">Linkcard</option>
            </select>
            <input type="text" id="mediaTitle" placeholder="Title">
            <input type="text" id="mediaUrl" placeholder="URL or Content">
            <button onclick="addMediaToChannel()">Add Media</button>

            <br><br>
            <h3>Current Media</h3>
            <div id="mediaList"></div>
        </div>
    </div>

    <script>
        let scheduleData = {};
        let currentBand = '';
        let currentIndex = -1;

        async function loadData() {
            const res = await fetch('/api/schedule');
            scheduleData = await res.json();
            populateChannelDropdown();
        }

        function populateChannelDropdown() {
            const select = document.getElementById('channelSelect');
            select.innerHTML = '<option value="">-- Select a Channel --</option>';

            ['vhf', 'uhf'].forEach(band => {
                scheduleData[band].forEach((ch, index) => {
                    const option = document.createElement('option');
                    option.value = `${band}-${index}`;
                    option.textContent = `${band.toUpperCase()} - ${ch.name}`;
                    select.appendChild(option);
                });
            });
        }

        function loadSelectedChannel() {
            const select = document.getElementById('channelSelect');
            const value = select.value;
            const form = document.getElementById('editForm');

            if (!value) {
                form.style.display = 'none';
                return;
            }

            const [band, index] = value.split('-');
            currentBand = band;
            currentIndex = parseInt(index);

            const ch = scheduleData[band][currentIndex];

            document.getElementById('editingTitle').textContent = `Editing: ${ch.name}`;
            document.getElementById('editName').value = ch.name;
            document.getElementById('editSchedule').value = ch.schedule || '';
            document.getElementById('editPresentation').value = ch.presentation || 'single';

            renderMediaList();
            form.style.display = 'block';
        }

        function renderMediaList() {
            const container = document.getElementById('mediaList');
            container.innerHTML = '';

            const ch = scheduleData[currentBand][currentIndex];
            if (!ch.media || ch.media.length === 0) {
                container.innerHTML = '<p style="color:#888;">No media yet.</p>';
                return;
            }

            ch.media.forEach((m, mIndex) => {
                const div = document.createElement('div');
                div.className = 'media-item';
                div.innerHTML = `
                    <span>${m.title || m.type} (${m.type})</span>
                    <button onclick="deleteMedia(${mIndex})">Delete</button>
                `;
                container.appendChild(div);
            });
        }

        async function saveChannelChanges() {
            const ch = scheduleData[currentBand][currentIndex];
            ch.name = document.getElementById('editName').value;
            ch.schedule = document.getElementById('editSchedule').value;
            ch.presentation = document.getElementById('editPresentation').value;

            await saveData();
            alert('Channel updated!');
            await loadData();
            populateChannelDropdown();
            
            // Re-select the channel
            document.getElementById('channelSelect').value = `${currentBand}-${currentIndex}`;
        }

        async function deleteSelectedChannel() {
            if (!confirm('Delete this channel?')) return;
            scheduleData[currentBand].splice(currentIndex, 1);
            await saveData();
            document.getElementById('editForm').style.display = 'none';
            await loadData();
            populateChannelDropdown();
        }

        async function addMediaToChannel() {
            const ch = scheduleData[currentBand][currentIndex];
            if (!ch.media) ch.media = [];

            const type = document.getElementById('mediaType').value;
            const title = document.getElementById('mediaTitle').value;
            const url = document.getElementById('mediaUrl').value;

            ch.media.push({ type, title, url });
            await saveData();
            renderMediaList();
            
            // Clear inputs
            document.getElementById('mediaTitle').value = '';
            document.getElementById('mediaUrl').value = '';
        }

        async function deleteMedia(mediaIndex) {
            if (!confirm('Delete this media item?')) return;
            scheduleData[currentBand][currentIndex].media.splice(mediaIndex, 1);
            await saveData();
            renderMediaList();
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
            await loadData();
            populateChannelDropdown();
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