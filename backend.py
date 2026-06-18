from flask import Flask, jsonify, request, render_template_string
import json
import os

app = Flask(__name__)

# =====================
# CONFIG
# =====================
ADMIN_PASSWORD = "MuffinBennett!987"   # Change this to something secure
SCHEDULE_FILE = "schedule.json"

# =====================
# HELPER FUNCTIONS
# =====================
def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {"vhf": [], "uhf": []}

def save_schedule(data):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# ROUTES
# =====================

@app.route('/api/schedule')
def get_schedule():
    data = load_schedule()
    return jsonify(data)

@app.route('/api/schedule', methods=['POST'])
def update_schedule():
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    new_data = request.get_json()
    if not new_data:
        return jsonify({"error": "No data provided"}), 400

    save_schedule(new_data)
    return jsonify({"message": "Schedule updated successfully"})

# =====================
# ADMIN PAGE (Basic)
# =====================
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Retro TV</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f4; }
        h1 { color: #333; }
        .section { margin-bottom: 40px; }
        .channel-card {
            background: white;
            border: 1px solid #ccc;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
        }
        .channel-card input, .channel-card textarea {
            width: 100%;
            padding: 8px;
            margin-top: 5px;
            box-sizing: border-box;
        }
        button {
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h1>Retro TV Admin Panel</h1>
    <p>Edit your channels below and click Save Changes.</p>

    <div class="section">
        <h2>VHF Channels</h2>
        <div id="vhf-channels"></div>
    </div>

    <div class="section">
        <h2>UHF Channels</h2>
        <div id="uhf-channels"></div>
    </div>

    <button onclick="saveChanges()">Save Changes</button>

    <script>
        let scheduleData = {};

        async function loadSchedule() {
            const res = await fetch('/api/schedule');
            scheduleData = await res.json();

            renderChannels('vhf', scheduleData.vhf || []);
            renderChannels('uhf', scheduleData.uhf || []);
        }

        function renderChannels(type, channels) {
            const container = document.getElementById(type + '-channels');
            container.innerHTML = '';

            channels.forEach((channel, index) => {
                const div = document.createElement('div');
                div.className = 'channel-card';
                div.innerHTML = `
                    <strong>Channel ${index + 2}</strong><br>
                    <label>Name:</label>
                    <input type="text" id="${type}-name-${index}" value="${channel.name || ''}"><br>
                    <label>Schedule / Content:</label>
                    <textarea id="${type}-schedule-${index}" rows="3">${channel.schedule || ''}</textarea>
                `;
                container.appendChild(div);
            });
        }

        async function saveChanges() {
            // Collect VHF data
            const vhf = [];
            const vhfContainer = document.getElementById('vhf-channels');
            const vhfCards = vhfContainer.children;

            for (let i = 0; i < vhfCards.length; i++) {
                const name = document.getElementById(`vhf-name-${i}`).value;
                const schedule = document.getElementById(`vhf-schedule-${i}`).value;
                vhf.push({
                    id: scheduleData.vhf[i].id,
                    name: name,
                    schedule: schedule
                });
            }

            // Collect UHF data
            const uhf = [];
            const uhfContainer = document.getElementById('uhf-channels');
            const uhfCards = uhfContainer.children;

            for (let i = 0; i < uhfCards.length; i++) {
                const name = document.getElementById(`uhf-name-${i}`).value;
                const schedule = document.getElementById(`uhf-schedule-${i}`).value;
                uhf.push({
                    id: scheduleData.uhf[i].id,
                    name: name,
                    schedule: schedule
                });
            }

            const updatedData = {
                vhf: vhf,
                uhf: uhf
            };

            try {
                const res = await fetch('/api/schedule?password={{ password }}', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedData)
                });

                const result = await res.json();
                alert(result.message || result.error);
            } catch (err) {
                alert("Error saving changes");
            }
        }

        // Load data when page loads
        loadSchedule();
    </script>
</body>
</html>
"""


@app.route('/admin')
def admin_page():
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return "Unauthorized", 401

    data = load_schedule()
    return render_template_string(
        ADMIN_HTML,
        schedule_json=json.dumps(data, indent=2),
        password=password
    )

# =====================
# RUN
# =====================
if __name__ == '__main__':
    app.run(debug=True)