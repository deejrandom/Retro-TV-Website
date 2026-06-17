from flask import Flask, jsonify, request, render_template_string
import json

app = Flask(__name__)

# Change this to your own password
ADMIN_PASSWORD = "yourpassword123"

def load_schedule():
    with open('schedule.json', 'r') as f:
        return json.load(f)

def save_schedule(data):
    with open('schedule.json', 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return "App is running!"

@app.route('/api/schedule')
def get_schedule():
    return jsonify(load_schedule())

@app.route('/test')
def test():
    return "Test route is working!"

@app.route('/admin')
def admin_page():
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "Unauthorized. Add ?password=yourpassword123 to the URL", 401

    schedule = load_schedule()
    return render_template_string(ADMIN_TEMPLATE, schedule=schedule)

@app.route('/api/schedule/save', methods=['POST'])
def save_schedule_api():
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    new_data = request.get_json()
    save_schedule(new_data)
    return jsonify({"success": True, "message": "Schedule saved successfully!"})

# Basic Admin HTML Template
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - Warren's Retro TV</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f4; }
        h1 { color: #333; }
        .channel { background: white; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; box-sizing: border-box; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h1>Retro TV Admin Panel</h1>
    <p><strong>Note:</strong> This is a basic version. We can improve it further.</p>

    <form id="adminForm">
        <h2>VHF Channels</h2>
        {% for i, ch in enumerate(schedule.vhf) %}
        <div class="channel">
            <strong>Channel {{ i + 2 }}</strong><br>
            Name: <input type="text" name="vhf_{{ i }}_name" value="{{ ch.name }}"><br>
            Schedule: <input type="text" name="vhf_{{ i }}_schedule" value="{{ ch.schedule }}"><br>
        </div>
        {% endfor %}

        <h2>UHF Channels</h2>
        {% for i, ch in enumerate(schedule.uhf) %}
        <div class="channel">
            <strong>Channel {{ i + 2 }}</strong><br>
            Name: <input type="text" name="uhf_{{ i }}_name" value="{{ ch.name }}"><br>
            Schedule: <input type="text" name="uhf_{{ i }}_schedule" value="{{ ch.schedule }}"><br>
            Content (optional):<br>
            <textarea name="uhf_{{ i }}_content" rows="3">{{ ch.content.html if ch.content else '' }}</textarea>
        </div>
        {% endfor %}

        <button type="button" onclick="saveChanges()">Save All Changes</button>
    </form>

    <script>
        async function saveChanges() {
            const form = document.getElementById('adminForm');
            const formData = new FormData(form);
            
            // Build the data object to send
            let newSchedule = { vhf: [], uhf: [] };

            // This is a simplified version - we'll improve it
            alert("Save feature is being improved. For now, manually edit schedule.json if needed.");
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
