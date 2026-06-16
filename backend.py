from flask import Flask, jsonify, request, render_template_string
import json
import os

app = Flask(__name__)

# Simple password protection (change this!)
ADMIN_PASSWORD = "MuffinBennett!987"

def load_schedule():
    with open('schedule.json', 'r') as f:
        return json.load(f)

def save_schedule(data):
    with open('schedule.json', 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/api/schedule')
def get_schedule():
    return jsonify(load_schedule())

@app.route('/admin')
def admin_page():
    # Very basic password check via query parameter for now
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "Unauthorized. Add ?password=yourpassword123 to the URL", 401

    schedule = load_schedule()
    return render_template_string(ADMIN_HTML, schedule=schedule)

@app.route('/api/schedule/save', methods=['POST'])
def save_schedule_route():
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    new_data = request.get_json()
    save_schedule(new_data)
    return jsonify({"success": True})

# Basic admin HTML template (we'll improve this)
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Retro TV</title>
</head>
<body>
    <h1>Retro TV Admin</h1>
    <p><strong>Note:</strong> This is a basic version. We can improve the interface later.</p>
    
    <form id="scheduleForm">
        <h2>VHF Channels</h2>
        {% for ch in schedule.vhf %}
        <div>
            <strong>{{ ch.name }}</strong><br>
            Schedule: <input type="text" name="vhf_{{ loop.index0 }}_schedule" value="{{ ch.schedule }}"><br><br>
        </div>
        {% endfor %}

        <h2>UHF Channels</h2>
        {% for ch in schedule.uhf %}
        <div>
            <strong>{{ ch.name }}</strong><br>
            Schedule: <input type="text" name="uhf_{{ loop.index0 }}_schedule" value="{{ ch.schedule }}"><br><br>
        </div>
        {% endfor %}

        <button type="button" onclick="saveSchedule()">Save Changes</button>
    </form>

    <script>
        async function saveSchedule() {
            const form = document.getElementById('scheduleForm');
            const formData = new FormData(form);
            
            // This is a simplified version - we'll improve it
            alert("Save feature coming in next step!");
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)