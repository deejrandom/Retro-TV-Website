from flask import Flask, jsonify, request, render_template_string, redirect, session, abort
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import secrets
import hmac

app = Flask(__name__)

# Only these sites may read the schedule from a browser.
# Override with a comma-separated CORS_ORIGINS env var on Render if you add another domain.
DEFAULT_ORIGINS = "https://warrencbennett.com,https://www.warrencbennett.com,http://localhost:8000,http://127.0.0.1:8000"
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', DEFAULT_ORIGINS).split(',') if o.strip()]
CORS(app, resources={r"/api/schedule": {"origins": ALLOWED_ORIGINS, "methods": ["GET"]}})

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Set it before starting the app.")
app.config['SECRET_KEY'] = SECRET_KEY

# Harden the login cookie. Render sets RENDER=true, so cookies are HTTPS-only there
# but still work when testing locally over plain http.
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get('RENDER'))

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD) if ADMIN_PASSWORD else None

SCHEDULE_FILE = '/data/schedule.json'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

# ---------- CSRF protection ----------
# Every admin page gets a secret token tied to the login session. Saves and logins
# must send it back, so another website can't trick your browser into making changes.
def get_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(32)
    return session['_csrf_token']

def check_csrf(sent_token):
    expected = session.get('_csrf_token')
    if not expected or not sent_token or not hmac.compare_digest(expected, sent_token):
        abort(400, description="Security token missing or expired. Reload the page and try again.")

@login_manager.unauthorized_handler
def unauthorized():
    # API calls get a clear 401 instead of being redirected to the login page
    if request.path.startswith('/api/'):
        return jsonify({"error": "Not logged in. Reload the page and log in again."}), 401
    return redirect('/login')

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {
            "vhf": [],
            "uhf": [],
            "guide_scroll_speed": 0.36,
            "crt_settings": {}
        }
        # Create the file on first run
        os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    # Ensure required keys exist (in case old data is missing them)
    if "vhf" not in data:
        data["vhf"] = []
    if "uhf" not in data:
        data["uhf"] = []
    if "guide_scroll_speed" not in data:
        data["guide_scroll_speed"] = 0.36
    if "crt_settings" not in data:
        data["crt_settings"] = {}
    
    return data

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
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
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

            <label>Channel Description (shown at the top of the channel; optional)</label>
            <textarea id="editDescription" rows="4"></textarea>

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
                <option value="archive">Archive.org Video</option>
                <option value="text">Text Block</option>
                <option value="linkcard">Linkcard</option>
            </select>

            <div id="normalFields">
                <input type="text" id="mediaTitle" placeholder="Title">
                <input type="text" id="mediaUrl" placeholder="URL or Link">
                <input type="text" id="mediaLink" placeholder="Link (where the card goes when clicked)" style="display:none;">
                <div id="imageFields">
                    <input type="text" id="mediaGroup" placeholder="Gallery Group (e.g. Final Fantasy) — blank = Uncategorized" list="groupOptions">
                    <datalist id="groupOptions"></datalist>
                    <label><input type="checkbox" id="mediaCover" style="width:auto;"> Use as the cover image for this group</label>
                </div>
            </div>

            <div id="textFields" class="text-fields">
                <input type="text" id="textTitle" placeholder="Optional Title">
                <textarea id="textContent" placeholder="Your text here..." rows="6"></textarea>
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
    </div>

    <script>
        let scheduleData = {};
        let currentBand = '';
        let currentIndex = -1;

        function renderMediaList() {
            const container = document.getElementById('mediaList');
            if (!container) return;
            container.innerHTML = '';
            refreshGroupOptions();

            const ch = scheduleData[currentBand][currentIndex];
            if (!ch || !ch.media || ch.media.length === 0) {
                container.innerHTML = '<p style="color:#888;">No media yet.</p>';
                return;
            }

            ch.media.forEach((m, mIndex) => {
                const div = document.createElement('div');
                div.className = 'media-item';

                const label = document.createElement('span');
                if (m.type === 'text') {
                    label.textContent = 'Text: ' + (m.title || 'Untitled');
                } else if (m.type === 'linkcard') {
                    label.textContent = 'Linkcard: ' + (m.title || 'Untitled') + (m.link ? '' : '  ⚠ no link');
                } else if (m.type === 'archive') {
                    label.textContent = 'Archive.org: ' + (m.title || m.url);
                } else if (m.type === 'image') {
                    label.textContent = 'Image: ' + (m.title || 'Untitled')
                        + '  [' + (m.gallery_group || 'Uncategorized') + ']'
                        + (m.is_group_cover ? '  ★ cover' : '');
                } else {
                    label.textContent = m.title || m.type;
                }

                const actions = document.createElement('div');
                if (m.type === 'text' || m.type === 'linkcard' || m.type === 'image') {
                    const editBtn = document.createElement('button');
                    editBtn.textContent = 'Edit';
                    editBtn.onclick = () => {
                        if (m.type === 'text') editTextBlock(mIndex);
                        else if (m.type === 'linkcard') editLinkcard(mIndex);
                        else editImage(mIndex);
                    };
                    actions.appendChild(editBtn);
                }

                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.style.background = '#cc4444';
                deleteBtn.style.color = 'white';
                deleteBtn.onclick = () => deleteMedia(mIndex);
                actions.appendChild(deleteBtn);

                div.appendChild(label);
                div.appendChild(actions);
                container.appendChild(div);
            });
        }

        // Only one cover per group: clear the flag on every other image in that group
        function setGroupCover(ch, group) {
            (ch.media || []).forEach(m => {
                if (m.type === 'image' && (m.gallery_group || '') === (group || '')) {
                    delete m.is_group_cover;
                }
            });
        }

        // Fill the Gallery Group suggestions with groups already used in this channel
        function refreshGroupOptions() {
            const list = document.getElementById('groupOptions');
            if (!list) return;
            list.innerHTML = '';
            const ch = scheduleData[currentBand] && scheduleData[currentBand][currentIndex];
            const groups = new Set((ch && ch.media || [])
                .filter(m => m.type === 'image' && m.gallery_group)
                .map(m => m.gallery_group));
            groups.forEach(g => {
                const opt = document.createElement('option');
                opt.value = g;
                list.appendChild(opt);
            });
        }

        function editImage(mediaIndex) {
            const ch = scheduleData[currentBand][currentIndex];
            const item = ch.media[mediaIndex];
            const container = document.getElementById('mediaList');
            container.innerHTML = '';

            const wrapper = document.createElement('div');
            wrapper.style.cssText = 'background:#1f2a1f; padding:15px; border:2px solid #39ff14;';

            const heading = document.createElement('h4');
            heading.textContent = 'Edit Image';
            wrapper.appendChild(heading);

            [['Title', 'editImgTitle', item.title || ''],
             ['Image URL', 'editImgUrl', item.url || ''],
             ['Gallery Group (blank = Uncategorized)', 'editImgGroup', item.gallery_group || '']
            ].forEach(([labelText, id, value]) => {
                const lbl = document.createElement('label');
                lbl.textContent = labelText;
                const input = document.createElement('input');
                input.type = 'text';
                input.id = id;
                input.value = value;
                if (id === 'editImgGroup') input.setAttribute('list', 'groupOptions');
                wrapper.appendChild(lbl);
                wrapper.appendChild(input);
            });

            const coverLabel = document.createElement('label');
            const coverBox = document.createElement('input');
            coverBox.type = 'checkbox';
            coverBox.id = 'editImgCover';
            coverBox.style.width = 'auto';
            coverBox.checked = !!item.is_group_cover;
            coverLabel.appendChild(coverBox);
            coverLabel.appendChild(document.createTextNode(' Use as the cover image for this group'));
            wrapper.appendChild(document.createElement('br'));
            wrapper.appendChild(coverLabel);
            wrapper.appendChild(document.createElement('br'));

            const saveBtn = document.createElement('button');
            saveBtn.textContent = 'Save Changes';
            saveBtn.onclick = async () => {
                const url = document.getElementById('editImgUrl').value.trim();
                if (!url) { alert("Please enter an image URL."); return; }
                const group = document.getElementById('editImgGroup').value.trim();
                item.title = document.getElementById('editImgTitle').value.trim();
                item.url = url;
                if (group) item.gallery_group = group; else delete item.gallery_group;
                if (document.getElementById('editImgCover').checked) {
                    setGroupCover(ch, group);
                    item.is_group_cover = true;
                } else {
                    delete item.is_group_cover;
                }
                await saveData();
                renderMediaList();
            };
            wrapper.appendChild(saveBtn);

            const cancelBtn = document.createElement('button');
            cancelBtn.textContent = 'Cancel';
            cancelBtn.style.background = '#555';
            cancelBtn.style.marginLeft = '10px';
            cancelBtn.onclick = () => renderMediaList();
            wrapper.appendChild(cancelBtn);

            container.appendChild(wrapper);
        }

        function editLinkcard(mediaIndex) {
            const item = scheduleData[currentBand][currentIndex].media[mediaIndex];
            const container = document.getElementById('mediaList');
            container.innerHTML = '';

            const wrapper = document.createElement('div');
            wrapper.style.cssText = 'background:#1f2a1f; padding:15px; border:2px solid #39ff14;';

            const heading = document.createElement('h4');
            heading.textContent = 'Edit Linkcard';
            wrapper.appendChild(heading);

            // Old linkcards stored the destination in "url" with no "link".
            // Pre-fill so nothing is lost: put that old value in the Link box.
            const hasLink = !!item.link;
            const fields = [
                ['Title', 'editLcTitle', item.title || ''],
                ['Image URL (optional)', 'editLcUrl', hasLink ? (item.url || '') : ''],
                ['Link (where the card goes)', 'editLcLink', hasLink ? item.link : (item.url || '')]
            ];
            fields.forEach(([labelText, id, value]) => {
                const lbl = document.createElement('label');
                lbl.textContent = labelText;
                const input = document.createElement('input');
                input.type = 'text';
                input.id = id;
                input.value = value;
                wrapper.appendChild(lbl);
                wrapper.appendChild(input);
            });

            const saveBtn = document.createElement('button');
            saveBtn.textContent = 'Save Changes';
            saveBtn.onclick = async () => {
                const link = document.getElementById('editLcLink').value.trim();
                if (!link) { alert("Please enter the link the card should go to."); return; }
                item.title = document.getElementById('editLcTitle').value.trim();
                item.url = document.getElementById('editLcUrl').value.trim();
                item.link = link;
                await saveData();
                renderMediaList();
            };
            wrapper.appendChild(saveBtn);

            const cancelBtn = document.createElement('button');
            cancelBtn.textContent = 'Cancel';
            cancelBtn.style.background = '#555';
            cancelBtn.style.marginLeft = '10px';
            cancelBtn.onclick = () => renderMediaList();
            wrapper.appendChild(cancelBtn);

            container.appendChild(wrapper);
        }

        function editTextBlock(mediaIndex) {
            const ch = scheduleData[currentBand][currentIndex];
            const item = ch.media[mediaIndex];
            const container = document.getElementById('mediaList');
            container.innerHTML = '';

            const wrapper = document.createElement('div');
            wrapper.style.cssText = 'background:#1f2a1f; padding:15px; border:2px solid #39ff14;';

            const heading = document.createElement('h4');
            heading.textContent = 'Edit Text Block';
            wrapper.appendChild(heading);

            const titleInput = document.createElement('input');
            titleInput.type = 'text';
            titleInput.id = 'editTextTitle';
            titleInput.value = item.title || '';
            titleInput.placeholder = 'Title';
            titleInput.style.width = '100%';
            wrapper.appendChild(titleInput);
            wrapper.appendChild(document.createElement('br'));
            wrapper.appendChild(document.createElement('br'));

            const contentArea = document.createElement('textarea');
            contentArea.id = 'editTextContent';
            contentArea.rows = 8;
            contentArea.style.width = '100%';
            contentArea.value = item.content || '';
            wrapper.appendChild(contentArea);
            wrapper.appendChild(document.createElement('br'));
            wrapper.appendChild(document.createElement('br'));

            const saveBtn = document.createElement('button');
            saveBtn.textContent = 'Save Changes';
            saveBtn.onclick = () => saveTextEdit(mediaIndex);
            wrapper.appendChild(saveBtn);

            const cancelBtn = document.createElement('button');
            cancelBtn.textContent = 'Cancel';
            cancelBtn.style.background = '#555';
            cancelBtn.style.marginLeft = '10px';
            cancelBtn.onclick = () => renderMediaList();
            wrapper.appendChild(cancelBtn);

            container.appendChild(wrapper);
        }

        async function saveTextEdit(mediaIndex) {
            const title = document.getElementById('editTextTitle').value;
            const content = document.getElementById('editTextContent').value;

            scheduleData[currentBand][currentIndex].media[mediaIndex].title = title;
            scheduleData[currentBand][currentIndex].media[mediaIndex].content = content;

            await saveData();
            renderMediaList();
        }

        async function loadData() {
            const res = await fetch('/api/schedule');
            scheduleData = await res.json();
            
            if (scheduleData.guide_scroll_speed) {
                document.getElementById('scrollSpeed').value = scheduleData.guide_scroll_speed;
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

            if (!channelSelect.value) {
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
            document.getElementById('editDescription').value = ch.description || '';

            renderMediaList();
            editSection.style.display = 'block';
        }

        function toggleMediaFields() {
            const type = document.getElementById('mediaType').value;
            document.getElementById('normalFields').style.display = (type === 'text') ? 'none' : 'block';
            const isLinkcard = (type === 'linkcard');
            document.getElementById('mediaLink').style.display = isLinkcard ? 'block' : 'none';
            document.getElementById('mediaUrl').placeholder = isLinkcard ? 'Image URL (optional)'
                : (type === 'archive') ? 'Archive.org link, e.g. https://archive.org/details/double-indemnity-1944-restored-movie-720p-hd'
                : 'URL or Link';
            document.getElementById('imageFields').style.display = (type === 'image') ? 'block' : 'none';
            document.getElementById('textFields').style.display = (type === 'text') ? 'block' : 'none';
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

                ch.media.push({ type: "text", title, content });
                document.getElementById('textTitle').value = '';
                document.getElementById('textContent').value = '';
            } else if (type === 'linkcard') {
                const title = document.getElementById('mediaTitle').value.trim();
                const url = document.getElementById('mediaUrl').value.trim();
                const link = document.getElementById('mediaLink').value.trim();

                if (!link) {
                    alert("Please enter the link the card should go to.");
                    return;
                }

                ch.media.push({ type, title, url, link });
                document.getElementById('mediaTitle').value = '';
                document.getElementById('mediaUrl').value = '';
                document.getElementById('mediaLink').value = '';
            } else {
                const title = document.getElementById('mediaTitle').value.trim();
                const url = document.getElementById('mediaUrl').value.trim();

                if (!url) {
                    alert("Please enter a URL.");
                    return;
                }
                if (type === 'archive' && !/archive\.org\/(details|embed)\/[A-Za-z0-9._-]+/.test(url)) {
                    alert("That doesn't look like an Archive.org video link. Copy the address from the video's archive.org page (it contains /details/).");
                    return;
                }

                const item = { type, title, url };
                if (type === 'image') {
                    const group = document.getElementById('mediaGroup').value.trim();
                    const isCover = document.getElementById('mediaCover').checked;
                    if (group) item.gallery_group = group;
                    if (isCover) {
                        setGroupCover(ch, group);
                        item.is_group_cover = true;
                    }
                    // Group box is left filled in so you can add several images to the same group in a row
                    document.getElementById('mediaCover').checked = false;
                }
                ch.media.push(item);
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
            const desc = document.getElementById('editDescription').value.trim();
            if (desc) ch.description = desc; else delete ch.description;

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
            scheduleData.guide_scroll_speed = parseFloat(document.getElementById('scrollSpeed').value);
            await saveData();
            alert('Scroll speed saved!');
        }

        const CSRF_TOKEN = {{ csrf_token|tojson }};

        async function saveData() {
            let res;
            try {
                res = await fetch('/api/schedule', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': CSRF_TOKEN },
                    body: JSON.stringify(scheduleData)
                });
            } catch (err) {
                alert('Could not reach the server. Your change was NOT saved.');
                throw err;
            }
            if (!res.ok) {
                let msg = 'Save failed (' + res.status + ').';
                try { msg = (await res.json()).error || msg; } catch (e) {}
                alert(msg + ' Your change was NOT saved.');
                throw new Error(msg);
            }
        }

        document.getElementById('addChannelForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const form = new FormData(this);
            const newChannel = {
                id: form.get('name').toLowerCase().replace(/\\s+/g, '-'),
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

        document.getElementById('mediaType').value = 'image';
        toggleMediaFields();
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
    check_csrf(request.headers.get('X-CSRF-Token'))
    new_data = request.get_json(silent=True)
    if not isinstance(new_data, dict):
        return jsonify({"error": "No data provided"}), 400
    # Refuse anything that would wipe out the channel lists
    if not isinstance(new_data.get('vhf'), list) or not isinstance(new_data.get('uhf'), list):
        return jsonify({"error": "Schedule must contain 'vhf' and 'uhf' channel lists"}), 400
    save_schedule(new_data)
    return jsonify({"message": "Saved successfully"})

@app.route('/admin')
@login_required
def admin():
    return render_template_string(ADMIN_HTML, csrf_token=get_csrf_token())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not ADMIN_PASSWORD_HASH:
        return "Admin login is not configured. Set the ADMIN_PASSWORD environment variable.", 503
    if request.method == 'POST':
        check_csrf(request.form.get('csrf_token'))
        password = request.form.get('password') or ''
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.clear()  # fresh session on login
            login_user(User("admin"))
            return redirect('/admin')
        return "Invalid password", 401
    return render_template_string(LOGIN_HTML, csrf_token=get_csrf_token())

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, port=5000)