from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)
CORS(app)

app.secret_key = "RetroTV_SecretKey_2026_FinalFix_XYZ987"

ADMIN_PASSWORD = "MuffinBennett!987"
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
# LOGIN
# =====================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Retro TV - Login</title>
    <style>
        body { background: #0a0a1f; color: #39ff14; font-family: 'Press Start 2P', cursive; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .login-box { background: #111; border: 6px solid #334455; padding: 40px; width: 420px; }
        h1 { color: #ffcc00; text-align: center; margin-bottom: 30px; }
        input { width: 100%; padding: 14px; margin: 10px 0; background: #222; border: 3px solid #556677; color: #fff; font-family: 'Press Start 2P', cursive; }
        button { width: 100%; padding: 16px; background: #39ff14; color: #000; border: none; font-family: 'Press Start 2P', cursive; font-weight: bold; cursor: pointer; margin-top: 20px; }
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
# ADMIN PAGE (FULL VERSION)
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

    <div class="section">
        <h2>Guide Scroll Speed</h2>
        <input type="number" id="scrollSpeed" step="0.05" value="0.36">
        <button onclick="saveScrollSpeed()">Save Speed</button>
        <p style="color:#aaa; font-size:12px;">Lower = slower. Recommended: 0.20 – 0.80</p>
    </div>

    <script>
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

        function renderMediaList(band, chIndex) {
            const container = document.getElementById(`media-list-${band}-${chIndex}`);
            if (!container) return;
            container.innerHTML = '';

            const ch = scheduleData[band][chIndex];
            if (!ch.media) ch.media = [];

            ch.media.forEach((m, mIndex) => {
                const item = document.createElement('div');
                item.style.border = '1px solid #555';
                item.style.padding = '8px';
                item.style.margin = '6px 0';
                item.innerHTML = `
                    <strong>${m.title || '(no title)'}</strong> [${m.type}]<br>
                    ${m.gallery_group ? `<small>Group: ${m.gallery_group}</small><br>` : ''}
                    ${m.is_group_cover ? `<span style="color:#ffcc00;">★ Cover</span><br>` : ''}
                    <button onclick="showEditMediaForm('${band}', ${chIndex}, ${mIndex}, this)">Edit</button>
                    <button onclick="deleteMedia('${band}', ${chIndex}, ${mIndex})" style="background:#ff4444; color:white;">Delete</button>
                `;
                container.appendChild(item);
            });
        }

        function showAddMediaForm(band, chIndex, button) {
            const formContainer = document.getElementById(`add-form-${band}-${chIndex}`);
            const ch = scheduleData[band][chIndex];
            const isGallery = ch.presentation === 'gallery';

            formContainer.innerHTML = `
                <strong>Add New Media</strong><br><br>
                Title: <input type="text" id="media-title-${band}-${chIndex}"><br>
                Type: 
                <select id="media-type-${band}-${chIndex}" onchange="toggleImageFields('${band}', ${chIndex})">
                    <option value="image">Image</option>
                    <option value="youtube">YouTube</option>
                    <option value="text">Text</option>
                </select><br>

                <div id="image-upload-section-${band}-${chIndex}">
                    <label><input type="radio" name="image-source-${band}-${chIndex}" value="url" checked> Image URL</label><br>
                    <input type="text" id="url-input-${band}-${chIndex}" placeholder="https://..."><br><br>
                </div>

                <div id="gallery-group-section-${band}-${chIndex}" style="display: ${isGallery ? 'block' : 'none'};">
                    Gallery Group: <input type="text" id="gallery-group-${band}-${chIndex}" placeholder="e.g. Final Fantasy">
                </div>

                <button onclick="saveNewMedia('${band}', ${chIndex})">Save Media</button>
                <button onclick="hideAddForm('${band}', ${chIndex})" style="background:#555;">Cancel</button>
            `;
            formContainer.classList.add('active');
        }

        function hideAddForm(band, chIndex) {
            const form = document.getElementById(`add-form-${band}-${chIndex}`);
            form.classList.remove('active');
            form.innerHTML = '';
        }

        function toggleImageFields(band, chIndex) {
            // Can expand later if needed
        }

        async function saveNewMedia(band, chIndex) {
            const ch = scheduleData[band][chIndex];
            const title = document.getElementById(`media-title-${band}-${chIndex}`).value;
            const type = document.getElementById(`media-type-${band}-${chIndex}`).value;
            const url = document.getElementById(`url-input-${band}-${chIndex}`).value;
            let group = "";

            if (ch.presentation === 'gallery' && type === 'image') {
                group = document.getElementById(`gallery-group-${band}-${chIndex}`).value || "";
            }

            if (!title || !url) return alert("Title and URL are required");

            if (!ch.media) ch.media = [];
            ch.media.push({
                title: title,
                type: type,
                url: url,
                gallery_group: group || undefined,
                is_group_cover: false
            });

            await saveSchedule();
            hideAddForm(band, chIndex);
            renderChannels();
        }

        function showEditMediaForm(band, chIndex, mIndex, buttonElement) {
            const ch = scheduleData[band][chIndex];
            const media = ch.media[mIndex];
            const isGallery = ch.presentation === 'gallery';

            const parent = buttonElement.parentElement;

            parent.innerHTML = `
                <strong>Edit Media</strong><br><br>
                Title: <input type="text" id="edit-title-${band}-${chIndex}-${mIndex}" value="${media.title || ''}"><br>
                Type: 
                <select id="edit-type-${band}-${chIndex}-${mIndex}">
                    <option value="image" ${media.type === 'image' ? 'selected' : ''}>Image</option>
                    <option value="youtube" ${media.type === 'youtube' ? 'selected' : ''}>YouTube</option>
                    <option value="text" ${media.type === 'text' ? 'selected' : ''}>Text</option>
                </select><br>
                URL: <input type="text" id="edit-url-${band}-${chIndex}-${mIndex}" value="${media.url || ''}"><br>

                <div style="display: ${isGallery && media.type === 'image' ? 'block' : 'none'};">
                    Gallery Group: <input type="text" id="edit-group-${band}-${chIndex}-${mIndex}" value="${media.gallery_group || ''}">
                </div>

                <label style="display:block; margin-top:10px;">
                    <input type="checkbox" id="is-group-cover-${band}-${chIndex}-${mIndex}" ${media.is_group_cover ? 'checked' : ''}> 
                    Set as Cover for this Group
                </label>

                <button onclick="saveEditedMedia('${band}', ${chIndex}, ${mIndex}, this)">Save Changes</button>
                <button onclick="renderChannels()" style="background:#555;">Cancel</button>
            `;
        }

        async function saveEditedMedia(band, chIndex, mIndex, buttonElement) {
            const ch = scheduleData[band][chIndex];
            const media = ch.media[mIndex];

            media.title = document.getElementById(`edit-title-${band}-${chIndex}-${mIndex}`).value;
            media.type = document.getElementById(`edit-type-${band}-${chIndex}-${mIndex}`).value;
            media.url = document.getElementById(`edit-url-${band}-${chIndex}-${mIndex}`).value;

            if (ch.presentation === 'gallery' && media.type === 'image') {
                media.gallery_group = document.getElementById(`edit-group-${band}-${chIndex}-${mIndex}`).value || undefined;
            }

            media.is_group_cover = document.getElementById(`is-group-cover-${band}-${chIndex}-${mIndex}`).checked;

            await saveSchedule();
            renderChannels();
        }

        async function deleteMedia(band, chIndex, mIndex) {
            if (!confirm("Delete this media item?")) return;
            scheduleData[band][chIndex].media.splice(mIndex, 1);
            await saveSchedule();
            renderChannels();
        }

        async function addChannel() {
            const band = document.getElementById('newBand').value;
            const name = document.getElementById('newChannelName').value;
            const schedule = document.getElementById('newChannelSchedule').value;
            const presentation = document.getElementById('newPresentation').value;

            if (!name) return alert("Channel name is required");

            if (!scheduleData[band]) scheduleData[band] = [];

            scheduleData[band].push({
                id: name.toLowerCase().replace(/\s+/g, '-'),
                name: name,
                schedule: schedule,
                presentation: presentation,
                media: []
            });

            await saveSchedule();
            loadSchedule();
        }

        function editChannel(band, index) {
            const ch = scheduleData[band][index];
            const newName = prompt("Channel Name:", ch.name);
            if (newName) ch.name = newName;

            const newSchedule = prompt("Schedule text:", ch.schedule || "");
            if (newSchedule !== null) ch.schedule = newSchedule;

            const newPres = prompt("Presentation (single / gallery / linkcards):", ch.presentation || "single");
            if (newPres) ch.presentation = newPres;

            saveSchedule();
            loadSchedule();
        }

        async function deleteChannel(band, index) {
            if (!confirm("Delete this channel?")) return;
            scheduleData[band].splice(index, 1);
            await saveSchedule();
            loadSchedule();
        }

        async function saveSchedule() {
            await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scheduleData)
            });
        }

        async function saveScrollSpeed() {
            scheduleData.guide_scroll_speed = parseFloat(document.getElementById('scrollSpeed').value);
            await saveSchedule();
            alert("Scroll speed saved!");
        }

        loadSchedule();
    </script>
</body>
</html>
"""

@app.route('/admin')
@login_required
def admin():
    return render_template_string(ADMIN_HTML)

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
    return jsonify({"message": "Saved"})

if __name__ == '__main__':
    app.run(debug=True)