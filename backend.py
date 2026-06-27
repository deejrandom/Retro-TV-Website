from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

app.secret_key = "RetroTV_SecretKey_2026_FixNow"

SCHEDULE_FILE = 'schedule.json'

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {"vhf": [], "uhf": []}

def save_schedule(data):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# ADMIN PAGE (No login required for now)
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
        input, select, button { background: #222; color: #fff; border: 2px solid #555; padding: 8px; margin: 6px 0; font-family: inherit; width: 100%; box-sizing: border-box; }
        button { background: #39ff14; color: #000; cursor: pointer; font-weight: bold; width: auto; padding: 10px 18px; }
        button:hover { background: #ffcc00; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>
    
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
                        <strong>${band.toUpperCase()} ${index + 2} • ${ch.name}</strong><br><br>
                        <button onclick="editChannel('${band}', ${index})">Edit</button>
                        <button onclick="deleteChannel('${band}', ${index})" style="background:#ff4444; color:white;">Delete</button>
                    `;
                    container.appendChild(div);
                });
            });
        }

        async function addChannel() {
            // Basic add channel function
            alert("Channel adding will be restored in the next version.");
        }

        function editChannel(band, index) {
            alert("Edit feature coming back soon.");
        }

        async function deleteChannel(band, index) {
            if (!confirm("Delete this channel?")) return;
            scheduleData[band].splice(index, 1);
            await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scheduleData)
            });
            loadSchedule();
        }

        async function saveScrollSpeed() {
            scheduleData.guide_scroll_speed = parseFloat(document.getElementById('scrollSpeed').value);
            await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scheduleData)
            });
            alert("Scroll speed saved!");
        }

        loadSchedule();
    </script>
</body>
</html>
"""

@app.route('/admin')
def admin():
    return render_template_string(ADMIN_HTML)

@app.route('/api/schedule')
def get_schedule():
    return jsonify(load_schedule())

@app.route('/api/schedule', methods=['POST'])
def update_schedule():
    new_data = request.get_json()
    if not new_data:
        return jsonify({"error": "No data"}), 400
    save_schedule(new_data)
    return jsonify({"message": "Saved"})

if __name__ == '__main__':
    app.run(debug=True)