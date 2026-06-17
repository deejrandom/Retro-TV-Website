from flask import Flask, jsonify, request, render_template_string
import json

app = Flask(__name__)

ADMIN_PASSWORD = "MuffinBennett!987"   # ← Change this if you want

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

# Fixed Admin Template (no enumerate)
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f4f4f4; }
        .channel { background: white; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Retro TV Admin</h1>

    <form id="adminForm">
        <h2>VHF Channels</h2>
        {% for ch in schedule.vhf %}
        <div class="channel">
            <strong>Channel {{ loop.index + 1 }}</strong><br>
            Name: <input type="text" name="vhf_{{ loop.index0 }}_name" value="{{ ch.name }}"><br>
            Schedule: <input type="text" name="vhf_{{ loop.index0 }}_schedule" value="{{ ch.schedule }}"><br>
        </div>
        {% endfor %}

        <h2>UHF Channels</h2>
        {% for ch in schedule.uhf %}
        <div class="channel">
            <strong>Channel {{ loop.index + 1 }}</strong><br>
            Name: <input type="text" name="uhf_{{ loop.index0 }}_name" value="{{ ch.name }}"><br>
            Schedule: <input type="text" name="uhf_{{ loop.index0 }}_schedule" value="{{ ch.schedule }}"><br>
        </div>
        {% endfor %}

        <button type="button" onclick="alert('Save feature coming next!')">Save Changes</button>
    </form>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
