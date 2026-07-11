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
    return {"vhf": [], "uhf": [], "guide_scroll_speed": 0.36, "crt_settings": {}}

def save_schedule(data):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# LOGIN
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
# ADMIN PAGE
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Retro TV</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 20px; max-width: 1100px; margin: 0 auto; }
        h1, h2, h3 { color: #ffcc00; }
        .section { background: #111; border: 3px solid #334455; padding: 20px; margin-bottom: 25px; }
        select, input, button, textarea { background: #222; color: #fff; border: 2px solid #555; padding: 10px; margin: 8px 0; width: 100%; box-sizing: border-box; font-family: inherit; }
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 12px 24px; }
        button:hover { background: #ffcc00; }
        .media-item { background: #1a1a1a; border: 1px solid #555; padding: 10px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; }
        #editSection { display: none; margin-top: 20px; }
        .now-toggle { margin: 15px 0; padding: 10px; background: #1a2a1a; border: 2px solid #39ff14; }
        .text-fields { display: none; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <p><a href="/logout" style="color:#ffcc00;">Logout</a></p>

    <!-- Add Channel -->
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
                <option value="single">Single</option>
                <option value="gallery">Gallery</option>
                <option value="linkcards">Linkcards</option>
            </select>
            <button type="submit">Add Channel</button>
        </form>
    </div>

    <!-- Edit Channel -->
    <div class="section">
        <h2>Edit Channel</h2>

        <label><strong>Step 1: Choose Band</strong></label>
        <select id="bandSelect" onchange="loadChannelsForBand()">
            <option value="">-- Select VHF or UHF --</option>
            <option value="vhf">VHF</option>
            <option value="uhf">UHF</option>
        </select>

        <label><strong>Step 2: Choose Channel</strong></label>
        <select id="channelSelect" onchange="loadSelectedChannel()" disabled>
            <option value="">-- Select Channel --</option>
        </select>

        <div id="editSection">
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

            <div class="now-toggle">
                <label>
                    <input type="checkbox" id="editNow"> 
                    <strong>Show "NOW" badge on guide</strong>
                </label>
            </div>

            <br>
            <button onclick="saveChannelChanges()">Save Channel</button>
            <button onclick="deleteSelectedChannel()" style="background:#cc4444; color:white;">Delete Channel</button>

            <br><br>
            <h3>Add Media</h3>
            <select id="mediaType" onchange="toggleMediaFields()">
                <option value="image">Image</option>
                <option value="youtube">YouTube / Video</option>
                <option value="text">Text Block</option>
                <option value="linkcard">Linkcard</option>
            </select>

            <!-- Normal fields -->
            <div id="normalFields">
                <input type="text" id="mediaTitle" placeholder="Title">
                <input type="text" id="mediaUrl" placeholder="URL or Link">
            </div>

            <!-- Text Block fields -->
            <div id="textFields" class="text-fields">
                <input type="text" id="textTitle" placeholder="Optional Title">
                <textarea id="textContent" placeholder="Your text here. Use **bold** and *italic*" rows="6"></textarea>
                <small style="color:#888;">Formatting: **bold**, *italic*, line breaks, - bullets</small>
            </div>

            <button onclick="addMedia()">Add Media</button>

            <br><br>
            <h3>Current Media</h3>
            <div id="mediaList"></div>
        </div>
    </div>

    <!-- Guide Scroll Speed -->
    <div class="section">
        <h2>Guide Scroll Speed</h2>
        <input type="number" id="scrollSpeed" step="0.05" min="0.1" max="2" style="width: 150px;">
        <button onclick="saveScrollSpeed()">Save Speed</button>
        <p style="color:#888; font-size:13px;">Lower = slower classic crawl. Recommended: 0.20 – 0.80</p>
    </div>

    <!-- CRT Settings -->
    <div class="section">
        <h2>CRT / Phosphor Settings</h2>
        <label><input type="checkbox" id="scanlines"> Enable Scanlines</label><br>
        <label><input type="checkbox" id="phosphor"> Enable Phosphor Glow</label><br><br>
        <label>Phosphor Intensity</label>
        <input type="range" id="phosphorIntensity" min="0" max="1" step="0.1" value="0.5">
        <button onclick="saveCRTSettings()">Save CRT Settings</button>
    </div>

    <script>
        let scheduleData = {};
        let currentBand = '';
        let currentIndex = -1;

        async function loadData() {
            const res = await fetch('/api/schedule');
            scheduleData = await res.json();
            
            if (scheduleData.guide_scroll_speed) {
                document.getElementById('scrollSpeed').value = scheduleData.guide_scroll_speed;
            }
            
            if (scheduleData.crt_settings) {
                const crt = scheduleData.crt_settings;
                document.getElementById('scanlines').checked = crt.scanlines || false;
                document.getElementById('phosphor').checked = crt.phosphor || false;
                document.getElementById('phosphorIntensity').value = crt.phosphorIntensity || 0.5;
            }
        }

        function loadChannelsForBand() {
            const band = document.getElementById('bandSelect').value;
            const channelSelect = document.getElementById('channelSelect');
            const editSection = document.getElementById('editSection');

            channelSelect.innerHTML = '<option value="">-- Select Channel --</option>';
            channelSelect.disabled = true;
            editSection.style.display = 'none';

            if (!band) return;

            currentBand = band;
            scheduleData[band].forEach((ch, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = ch.name;
                channelSelect.appendChild(option);
            });

            channelSelect.disabled = false;
        }

        function loadSelectedChannel() {
            const channelSelect = document.getElementById('channelSelect');
            const editSection = document.getElementById('editSection');

            if (!channelSelect.value || channelSelect.value === "") {
                editSection.style.display = 'none';
                return;
            }

            currentIndex = parseInt(channelSelect.value);
            const ch = scheduleData[currentBand][currentIndex];

            document.getElementById('editingTitle').textContent = `Editing: ${ch.name}`;
            document.getElementById('editName').value = ch.name;
            document.getElementById('editSchedule').value = ch.schedule || '';
            document.getElementById('editPresentation').value = ch.presentation || 'single';
            document.getElementById('editNow').checked = ch.now || false;

            renderMediaList();
            editSection.style.display = 'block';
        }

        function toggleMediaFields() {
            const type = document.getElementById('mediaType').value;
            const normal = document.getElementById('normalFields');
            const text = document.getElementById('textFields');

            if (type === 'text') {
                normal.style.display = 'none';
                text.style.display = 'block';
            } else {
                normal.style.display = 'block';
                text.style.display = 'none';
            }
        }

        async function addMedia() {
            const ch = scheduleData[currentBand][currentIndex];
            if (!ch.media) ch.media = [];

            const type = document.getElementById('mediaType').value;

            if (type === 'text') {
                const title = document.getElementById('textTitle').value.trim();
                const content = document.getElementById('textContent').value.trim();

                if (!content) {
                    alert("Please enter some text content.");
                    return;
                }

                ch.media.push({
                    type: "text",
                    title: title || "",
                    content: content
                });

                document.getElementById('textTitle').value = '';
                document.getElementById('textContent').value = '';

            } else {
                const title = document.getElementById('mediaTitle').value.trim();
                const url = document.getElementById('mediaUrl').value.trim();

                if (!url) {
                    alert("Please enter a URL.");
                    return;
                }

                ch.media.push({ type, title, url });
                document.getElementById('mediaTitle').value = '';
                document.getElementById('mediaUrl').value = '';
            }

            await saveData();
            renderMediaList();
        }

        async function deleteMedia(mediaIndex) {
            if (!confirm('Delete this media?')) return;
            scheduleData[currentBand][currentIndex].media.splice(mediaIndex, 1);
            await saveData();
            renderMediaList();
        }

        async function saveChannelChanges() {
            const ch = scheduleData[currentBand][currentIndex];
            ch.name = document.getElementById('editName').value;
            ch.schedule = document.getElementById('editSchedule').value;
            ch.presentation = document.getElementById('editPresentation').value;
            ch.now = document.getElementById('editNow').checked;

            await saveData();
            alert('Channel saved!');
            await loadData();
        }

        async function deleteSelectedChannel() {
            if (!confirm('Delete this channel?')) return;
            scheduleData[currentBand].splice(currentIndex, 1);
            await saveData();
            document.getElementById('editSection').style.display = 'none';
            document.getElementById('channelSelect').innerHTML = '<option value="">-- Select Channel --</option>';
            await loadData();
        }

        async function saveScrollSpeed() {
            const speed = parseFloat(document.getElementById('scrollSpeed').value);
            scheduleData.guide_scroll_speed = speed;
            await saveData();
            alert('Scroll speed saved!');
        }

        async function saveCRTSettings() {
            if (!scheduleData.crt_settings) scheduleData.crt_settings = {};

            scheduleData.crt_settings.scanlines = document.getElementById('scanlines').checked;
            scheduleData.crt_settings.phosphor = document.getElementById('phosphor').checked;
            scheduleData.crt_settings.phosphorIntensity = parseFloat(document.getElementById('phosphorIntensity').value);

            await saveData();
            alert('CRT settings saved!');
        }

        async function saveData() {
            await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scheduleData)
            });
        }

        document.getElementById('addChannelForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const form = new FormData(this);
            const newChannel = {
                id: form.get('name').toLowerCase().replace(/\s+/g, '-'),
                name: form.get('name'),
                schedule: form.get('schedule'),
                presentation: form.get('presentation'),
                media: [],
                now: false
            };
            scheduleData[form.get('band')].push(newChannel);
            await saveData();
            this.reset();
            await loadData();
        });

        // Initialize
        document.getElementById('mediaType').value = 'image';
        toggleMediaFields();
        document.getElementById('textFields').style.display = 'none';

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