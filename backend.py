from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os

app = Flask(__name__)
CORS(app)
app.secret_key = "RetroTV_SuperSecretKey_2026_XYZ123"

ADMIN_PASSWORD = "MuffinBennett!987"
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

# =====================
# DEFAULT SCHEDULE
# =====================
DEFAULT_SCHEDULE = {
    "guide_scroll_speed": 0.36,
    "vhf": [
        {"id": "home", "name": "HOME", "schedule": "Welcome to Warren C. Bennett's Retro Future", "presentation": "single", "media": []},
        {"id": "writing", "name": "WRITING", "schedule": "Random Encounters", "presentation": "single", "media": []},
        {"id": "games", "name": "GAMES", "schedule": "Retro gaming hub", "presentation": "single", "media": []},
        {
            "id": "pixelart",
            "name": "PIXEL ART",
            "schedule": "Pixel Art Galleries",
            "presentation": "gallery",
            "media": [
                {"title": "Final Fantasy Logo", "type": "image", "url": "https://warrencbennett.com/Final%20Fantasy%20Images/ff-Logo-NES.webp", "gallery_group": "Final Fantasy", "is_group_cover": True},
                {"title": "Black Mage", "type": "image", "url": "https://warrencbennett.com/Final%20Fantasy%20Images/black-mage-nes.png", "gallery_group": "Final Fantasy"},
                {"title": "Red Mage", "type": "image", "url": "https://warrencbennett.com/Final%20Fantasy%20Images/redmage-nes.png", "gallery_group": "Final Fantasy"},
                {"title": "White Mage", "type": "image", "url": "https://warrencbennett.com/Final%20Fantasy%20Images/white-mage-nes.png", "gallery_group": "Final Fantasy"}
            ]
        },
        {"id": "films", "name": "FILMS", "schedule": "Film related content", "presentation": "single", "media": []},
        {"id": "tv", "name": "TV", "schedule": "TV related content", "presentation": "single", "media": []},
        {"id": "where", "name": "WHERE CAN YOU FIND ME?", "schedule": "Social links", "presentation": "single", "media": []}
    ],
    "uhf": [
        {"id": "uhf1", "name": "CARTOONS", "schedule": "Public Domain Cartoons", "presentation": "single", "media": []},
        {"id": "uhf2", "name": "CARTOONS", "schedule": "More Public Domain Cartoons", "presentation": "single", "media": []},
        {"id": "uhf3", "name": "TV SHOWS", "schedule": "Classic Public Domain TV", "presentation": "single", "media": []},
        {"id": "uhf4", "name": "TV SHOWS", "schedule": "More Classic TV", "presentation": "single", "media": []},
        {"id": "uhf5", "name": "FILMS", "schedule": "Double Indemnity - All day", "presentation": "single", "media": [
            {"title": "Double Indemnity (1944)", "type": "youtube", "url": "https://www.youtube.com/watch?v=wI5xaum_HlA"}
        ]},
        {"id": "uhf6", "name": "FILMS", "schedule": "More Public Domain Films", "presentation": "single", "media": []}
    ]
}

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            data = json.load(f)
        if not data.get("vhf") or len(data.get("vhf", [])) == 0:
            save_schedule(DEFAULT_SCHEDULE)
            return DEFAULT_SCHEDULE
        return data
    save_schedule(DEFAULT_SCHEDULE)
    return DEFAULT_SCHEDULE

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
    <title>Login - Retro TV Admin</title>
    <style>
        body { background: #0a0a1f; color: #39ff14; font-family: 'Press Start 2P', system-ui; padding: 60px; text-align: center; }
        input { padding: 14px; font-size: 20px; width: 300px; background: #111; color: #fff; border: 3px solid #556677; }
        button { padding: 14px 30px; font-size: 20px; background: #39ff14; color: #000; border: none; cursor: pointer; margin-top: 20px; }
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
# FULL ADMIN PAGE (WITH ADD/DELETE CHANNEL)
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Retro TV Admin</title>
    <style>
        body { font-family: 'Press Start 2P', system-ui; background: #0a0a1f; color: #39ff14; padding: 30px; max-width: 1100px; margin: 0 auto; }
        h1, h2 { color: #ffcc00; }
        .section { background: #111; border: 3px solid #334455; padding: 20px; margin-bottom: 30px; }
        input, select, button { background: #222; color: #fff; border: 2px solid #556677; padding: 10px; margin: 8px 0; font-family: inherit; width: 100%; box-sizing: border-box; }
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 10px 20px; }
        button:hover { background: #ffcc00; }
        .media-item { background: #1a1a1a; border: 2px solid #444; padding: 15px; margin: 12px 0; }
        .success { color: #39ff14; background: #112211; border: 2px solid #39ff14; padding: 12px; margin: 15px 0; }
        .error { color: #ff6666; background: #331111; border: 2px solid #ff6666; padding: 12px; margin: 15px 0; }
        label { display: block; margin-top: 12px; color: #ffcc00; }
        .danger-btn { background: #aa3333; color: white; }
    </style>
</head>
<body>
    <h1>Retro TV Admin Panel</h1>

    <!-- ADD NEW CHANNEL -->
    <div class="section">
        <h2>Add New Channel</h2>
        <label>Band</label>
        <select id="newBand">
            <option value="vhf">VHF</option>
            <option value="uhf">UHF</option>
        </select>
        
        <label>Channel Name</label>
        <input type="text" id="newChannelName" placeholder="e.g. Retro Gaming">
        
        <label>Schedule / Description (optional)</label>
        <input type="text" id="newChannelSchedule" placeholder="What's on this channel?">
        
        <button onclick="addNewChannel()">+ Add Channel</button>
    </div>

    <!-- SELECT CHANNEL -->
    <div class="section">
        <h2>1. Select Channel</h2>
        <div>
            <label>Band:</label>
            <select id="bandSelect" onchange="loadChannels()">
                <option value="vhf">VHF</option>
                <option value="uhf">UHF</option>
            </select>
            
            <label>Channel:</label>
            <select id="channelSelect" onchange="loadSelectedChannel()">
                <option value="">-- Select a channel --</option>
            </select>
        </div>
    </div>

    <!-- EDIT CHANNEL -->
    <div class="section" id="channelEditor" style="display:none;">
        <h2>2. Edit Channel</h2>
        
        <label>Channel Name</label>
        <input type="text" id="channelName">
        
        <label>Schedule / Description</label>
        <input type="text" id="channelSchedule">
        
        <label>Presentation Mode</label>
        <select id="presentationMode">
            <option value="single">Single (normal content)</option>
            <option value="gallery">Gallery (grouped images)</option>
            <option value="linkcards">Link Cards</option>
        </select>
        
        <button onclick="saveChannelChanges()">Save Channel Changes</button>
        
        <button onclick="deleteCurrentChannel()" class="danger-btn" style="margin-top: 20px;">Delete This Channel</button>

        <h3 style="margin-top:30px;">Media Items</h3>
        <div id="mediaList"></div>
        
        <h3 style="margin-top:30px;">Add New Media</h3>
        <label>Media Type</label>
        <select id="newMediaType" onchange="toggleMediaFields()">
            <option value="image">Image</option>
            <option value="youtube">YouTube Video</option>
            <option value="text">Text / Writing</option>
            <option value="linkcard">Link Card</option>
        </select>
        
        <div id="mediaFields">
            <label>Title</label>
            <input type="text" id="newMediaTitle">
            
            <label id="urlLabel">URL / Content</label>
            <input type="text" id="newMediaUrl">
            
            <div id="galleryFields" style="display:none;">
                <label>Gallery Group Name</label>
                <input type="text" id="newGalleryGroup" placeholder="e.g. Final Fantasy">
                <label><input type="checkbox" id="isCover"> Make this the cover image</label>
            </div>
        </div>
        
        <button onclick="addNewMedia()" style="margin-top:10px;">+ Add Media</button>
    </div>

    <!-- SCROLL SPEED -->
    <div class="section">
        <h2>3. Guide Scroll Speed</h2>
        <input type="number" id="scrollSpeed" step="0.05" min="0.1" max="1.5" style="width:150px;">
        <button onclick="saveScrollSpeed()">Save Scroll Speed</button>
        <p style="color:#aaa; font-size:13px;">Lower = slower classic crawl. Recommended: 0.20 – 0.80</p>
    </div>

    <div id="statusMessage"></div>

    <script>
        let scheduleData = {};
        let currentBand = '';
        let currentIndex = -1;

        async function loadSchedule() {
            const res = await fetch('/api/schedule');
            scheduleData = await res.json();
        }

        function loadChannels() {
            const band = document.getElementById('bandSelect').value;
            const select = document.getElementById('channelSelect');
            select.innerHTML = '<option value="">-- Select a channel --</option>';
            
            if (scheduleData[band]) {
                scheduleData[band].forEach((ch, i) => {
                    const opt = document.createElement('option');
                    opt.value = i;
                    opt.textContent = `${band.toUpperCase()} ${i+2} - ${ch.name}`;
                    select.appendChild(opt);
                });
            }
            document.getElementById('channelEditor').style.display = 'none';
        }

        function loadSelectedChannel() {
            const band = document.getElementById('bandSelect').value;
            const index = parseInt(document.getElementById('channelSelect').value);
            if (isNaN(index)) return;

            currentBand = band;
            currentIndex = index;
            const ch = scheduleData[band][index];

            document.getElementById('channelName').value = ch.name || '';
            document.getElementById('channelSchedule').value = ch.schedule || '';
            document.getElementById('presentationMode').value = ch.presentation || 'single';

            renderMediaList();
            document.getElementById('channelEditor').style.display = 'block';
            toggleMediaFields();
        }

        function renderMediaList() {
            const container = document.getElementById('mediaList');
            container.innerHTML = '';
            const ch = scheduleData[currentBand][currentIndex];
            if (!ch.media || ch.media.length === 0) {
                container.innerHTML = '<p style="color:#888;">No media yet.</p>';
                return;
            }

            ch.media.forEach((m, i) => {
                const div = document.createElement('div');
                div.className = 'media-item';
                div.innerHTML = `
                    <strong>${m.title || '(no title)'}</strong> 
                    <span style="color:#888;">[${m.type}]</span><br>
                    <small style="color:#aaa;">${m.url ? m.url.substring(0,80) : ''}</small><br><br>
                    <button onclick="editMedia(${i})">Edit</button>
                    <button onclick="deleteMedia(${i})" style="background:#aa3333; color:white;">Delete</button>
                `;
                container.appendChild(div);
            });
        }

        function toggleMediaFields() {
            const type = document.getElementById('newMediaType').value;
            document.getElementById('galleryFields').style.display = (type === 'image') ? 'block' : 'none';
        }

        async function addNewChannel() {
            const band = document.getElementById('newBand').value;
            const name = document.getElementById('newChannelName').value.trim();
            const schedule = document.getElementById('newChannelSchedule').value.trim();

            if (!name) {
                alert("Channel name is required.");
                return;
            }

            const newChannel = {
                id: name.toLowerCase().replace(/\s+/g, '-'),
                name: name,
                schedule: schedule || "New channel",
                presentation: "single",
                media: []
            };

            if (!scheduleData[band]) scheduleData[band] = [];
            scheduleData[band].push(newChannel);

            await saveSchedule();
            showStatus("Channel added successfully!", true);
            
            // Refresh dropdown
            document.getElementById('bandSelect').value = band;
            loadChannels();
            
            // Clear form
            document.getElementById('newChannelName').value = '';
            document.getElementById('newChannelSchedule').value = '';
        }

        async function deleteCurrentChannel() {
            if (!confirm("Are you sure you want to delete this channel?")) return;

            scheduleData[currentBand].splice(currentIndex, 1);
            await saveSchedule();
            showStatus("Channel deleted.", true);
            
            document.getElementById('channelEditor').style.display = 'none';
            loadChannels();
        }

        async function addNewMedia() {
            const type = document.getElementById('newMediaType').value;
            const title = document.getElementById('newMediaTitle').value.trim();
            const url = document.getElementById('newMediaUrl').value.trim();
            const group = document.getElementById('newGalleryGroup').value.trim();
            const isCover = document.getElementById('isCover').checked;

            if (!title || !url) {
                alert("Title and URL are required.");
                return;
            }

            const newMedia = { title, type, url };
            if (type === 'image' && group) {
                newMedia.gallery_group = group;
                if (isCover) newMedia.is_group_cover = true;
            }

            if (!scheduleData[currentBand][currentIndex].media) {
                scheduleData[currentBand][currentIndex].media = [];
            }
            scheduleData[currentBand][currentIndex].media.push(newMedia);

            await saveSchedule();
            renderMediaList();
            
            document.getElementById('newMediaTitle').value = '';
            document.getElementById('newMediaUrl').value = '';
            document.getElementById('newGalleryGroup').value = '';
            document.getElementById('isCover').checked = false;
        }

        async function deleteMedia(mediaIndex) {
            if (!confirm("Delete this media item?")) return;
            scheduleData[currentBand][currentIndex].media.splice(mediaIndex, 1);
            await saveSchedule();
            renderMediaList();
        }

        function editMedia(mediaIndex) {
            const m = scheduleData[currentBand][currentIndex].media[mediaIndex];
            const newTitle = prompt("New title:", m.title || '');
            if (newTitle !== null) m.title = newTitle;

            const newUrl = prompt("New URL / content:", m.url || '');
            if (newUrl !== null) m.url = newUrl;

            if (m.type === 'image') {
                const newGroup = prompt("Gallery Group:", m.gallery_group || '');
                if (newGroup !== null) m.gallery_group = newGroup;
            }

            saveSchedule();
            renderMediaList();
        }

        async function saveChannelChanges() {
            const ch = scheduleData[currentBand][currentIndex];
            ch.name = document.getElementById('channelName').value.trim();
            ch.schedule = document.getElementById('channelSchedule').value.trim();
            ch.presentation = document.getElementById('presentationMode').value;

            await saveSchedule();
            showStatus("Channel saved successfully!", true);
            loadChannels();
        }

        async function saveScrollSpeed() {
            const speed = parseFloat(document.getElementById('scrollSpeed').value);
            scheduleData.guide_scroll_speed = speed;
            await saveSchedule();
            showStatus("Scroll speed saved!", true);
        }

        async function saveSchedule() {
            const res = await fetch('/api/schedule?password=' + encodeURIComponent('MuffinBennett!987'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scheduleData)
            });
            if (!res.ok) {
                showStatus("Failed to save changes", false);
            }
        }

        function showStatus(msg, success) {
            const div = document.getElementById('statusMessage');
            div.className = success ? 'success' : 'error';
            div.textContent = msg;
            div.style.display = 'block';
            setTimeout(() => { div.style.display = 'none'; }, 4000);
        }

        async function initAdmin() {
            await loadSchedule();
            document.getElementById('scrollSpeed').value = scheduleData.guide_scroll_speed || 0.36;
            loadChannels();
        }

        initAdmin();
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            user = User("admin")
            login_user(user)
            return redirect('/admin')
        return "Invalid password", 401
    return render_template_string(LOGIN_HTML)

@app.route('/admin')
@login_required
def admin():
    return render_template_string(ADMIN_HTML)

if __name__ == '__main__':
    app.run(debug=True)