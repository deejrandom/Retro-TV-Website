from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'your-secret-key-change-this-to-something-strong'

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
        input { background: #222; color: white; border: 2px solid #555; padding: 12px; font-size: 18px; width: 300px; }
        button { background: #39ff14; color: black; border: none; padding: 12px 30px; font-size: 18px; cursor: pointer; margin-top: 20px; }
        button:hover { background: #ffcc00; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <form method="POST">
        <input type="password" name="password" placeholder="Enter Admin Password" required><br>
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
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 8px 16px; }
        button:hover { background: #ffcc00; }
        .success { color: #39ff14; font-weight: bold; padding: 10px; background: #112211; border: 2px solid #39ff14; margin: 15px 0; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    
    <div class="section">
        <h2>Edit Channel</h2>
        <select id="channelSelect" onchange="loadSelectedChannel()">
            <option value="">-- Select a Channel --</option>
        </select>

        <div id="editForm" style="display:none; margin-top:20px;">
            <label>Channel Name:</label>
            <input type="text" id="channelName">

            <label>Schedule:</label>
            <input type="text" id="channelSchedule">

            <label>Description:</label>
            <textarea id="channelDescription" rows="4"></textarea>

            <label>Presentation:</label>
            <select id="channelPresentation">
                <option value="single">Single</option>
                <option value="gallery">Gallery</option>
                <option value="linkcards">Link Cards</option>
            </select>

            <br><br>
            <button onclick="saveChannelChanges()">Save Changes</button>
        </div>
    </div>

    <div id="statusMessage" class="success" style="display:none;"></div>

    <script>
        let scheduleData = { vhf: [], uhf: [] };
        let currentType = '';
        let currentIndex = -1;

        async function loadSchedule() {
            const res = await fetch('/api/schedule');
            scheduleData = await res.json();
            populateDropdown();
        }

        function populateDropdown() {
            const select = document.getElementById('channelSelect');
            select.innerHTML = '<option value="">-- Select a Channel --</option>';
            
            scheduleData.vhf.forEach((ch, i) => {
                const opt = document.createElement('option');
                opt.value = `vhf-${i}`;
                opt.textContent = `VHF: ${ch.name}`;
                select.appendChild(opt);
            });
            
            scheduleData.uhf.forEach((ch, i) => {
                const opt = document.createElement('option');
                opt.value = `uhf-${i}`;
                opt.textContent = `UHF: ${ch.name}`;
                select.appendChild(opt);
            });
        }

        function loadSelectedChannel() {
            const value = document.getElementById('channelSelect').value;
            if (!value) {
                document.getElementById('editForm').style.display = 'none';
                return;
            }
            const [type, index] = value.split('-');
            currentType = type;
            currentIndex = parseInt(index);

            const ch = scheduleData[type][currentIndex];
            document.getElementById('channelName').value = ch.name || '';
            document.getElementById('channelSchedule').value = ch.schedule || '';
            document.getElementById('channelDescription').value = ch.description || '';
            document.getElementById('channelPresentation').value = ch.presentation || 'single';
            document.getElementById('editForm').style.display = 'block';
        }

        async function saveChannelChanges() {
            const ch = scheduleData[currentType][currentIndex];
            ch.name = document.getElementById('channelName').value;
            ch.schedule = document.getElementById('channelSchedule').value;
            ch.description = document.getElementById('channelDescription').value;
            ch.presentation = document.getElementById('channelPresentation').value;

            const status = document.getElementById('statusMessage');
            status.style.display = 'block';
            status.innerText = 'Saving...';

            await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scheduleData)
            });

            status.innerText = 'Saved!';
            setTimeout(() => status.style.display = 'none', 2000);
            await loadSchedule();
        }

        loadSchedule();
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