from flask import Flask, jsonify, request, render_template_string
import json

app = Flask(__name__)

ADMIN_PASSWORD = "MuffinBennett!987"

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
        return "Unauthorized", 401

    schedule = load_schedule()
    return render_template_string(ADMIN_TEMPLATE, schedule=schedule)

@app.route('/api/schedule/save', methods=['POST'])
def save_schedule_api():
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    new_data = request.get_json()
    save_schedule(new_data)
    return jsonify({"success": True})

# Admin Template with working Save button
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f4f4f4; }
        .channel { background: white; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
        input { width: 100%; padding: 8px; margin: 5px 0; }
        button { background: #28a745; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #218838; }
    </style>
</head>
<body>
    <h1>Retro TV Admin Panel</h1>
    <p>Edit the fields below, then click Save.</p>

    <form id="adminForm">
        <h2>VHF Channels</h2>
        {% for i in range(schedule.vhf|length) %}
        <div class="channel">
            <strong>Channel {{ i + 2 }}</strong><br>
            Name: <input type="text" name="vhf_{{ i }}_name" value="{{ schedule.vhf[i].name }}"><br>
            Schedule: <input type="text" name="vhf_{{ i }}_schedule" value="{{ schedule.vhf[i].schedule }}"><br>
        </div>
        {% endfor %}

        <h2>UHF Channels</h2>
        {% for i in range(schedule.uhf|length) %}
        <div class="channel">
            <strong>Channel {{ i + 2 }}</strong><br>
            Name: <input type="text" name="uhf_{{ i }}_name" value="{{ schedule.uhf[i].name }}"><br>
            Schedule: <input type="text" name="uhf_{{ i }}_schedule" value="{{ schedule.uhf[i].schedule }}"><br>
        </div>
        {% endfor %}

        <button type="button" onclick="saveChanges()">Save Changes</button>
    </form>

    <script>
        async function saveChanges() {
            const form = document.getElementById('adminForm');
            const formData = new FormData(form);
            let newSchedule = { vhf: [], uhf: [] };

            // Build VHF data
            {% for i in range(schedule.vhf|length) %}
            newSchedule.vhf.push({
                id: "{{ schedule.vhf[i].id }}",
                name: formData.get("vhf_{{ i }}_name"),
                schedule: formData.get("vhf_{{ i }}_schedule")
            });
            {% endfor %}

            // Build UHF data
            {% for i in range(schedule.uhf|length) %}
            newSchedule.uhf.push({
                id: "{{ schedule.uhf[i].id }}",
                name: formData.get("uhf_{{ i }}_name"),
                schedule: formData.get("uhf_{{ i }}_schedule")
            });
            {% endfor %}

            const response = await fetch('/api/schedule/save?password=MuffinBennett!987', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newSchedule)
            });

            if (response.ok) {
                alert("Changes saved successfully!");
            } else {
                alert("Error saving changes.");
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
