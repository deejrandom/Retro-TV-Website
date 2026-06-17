from flask import Flask, jsonify, request, render_template_string
import json

app = Flask(__name__)

# ====================== CONFIG ======================
ADMIN_PASSWORD = "MuffinBennett!987"   # Change this to your own password

def load_schedule():
    with open('schedule.json', 'r') as f:
        return json.load(f)

def save_schedule(data):
    with open('schedule.json', 'w') as f:
        json.dump(data, f, indent=2)

# ====================== ROUTES ======================
@app.route('/api/schedule')
def get_schedule():
    return jsonify(load_schedule())

@app.route('/admin')
def admin_page():
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return "Unauthorized. Add ?password=YOUR_PASSWORD to the URL", 401

    schedule = load_schedule()
    return render_template_string(ADMIN_HTML, schedule=schedule)

@app.route('/api/schedule/save', methods=['POST'])
def save_schedule_route():
    password = request.args.get('password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    new_data = request.get_json()
    save_schedule(new_data)
    return jsonify({"success": True, "message": "Changes saved successfully!"})

# ====================== ADMIN HTML ======================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Retro TV Admin</title>
    <style>
        body { font-family: Arial, sans-serif; background: #111; color: #eee; padding: 20px; max-width: 900px; margin: 0 auto; }
        h1 { color: #0ff; }
        .section { background: #222; padding: 20px; margin-bottom: 30px; border-radius: 10px; }
        input, textarea { width: 100%; padding: 10px; margin: 6px 0; background: #333; color: #fff; border: 1px solid #555; border-radius: 5px; }
        button { background: #0ff; color: #000; padding: 14px 30px; font-size: 16px; border: none; border-radius: 6px; cursor: pointer; margin-top: 20px; }
        button:hover { background: #0cc; }
        .channel { background: #1a1a1a; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>Retro TV Admin Panel</h1>
    <p>Edit your channels and guide date below. Click Save when finished.</p>

    <form id="adminForm">
        <!-- GUIDE DATE -->
        <div class="section">
            <h2>Program Guide Date</h2>
            <input type="text" name="guide_date" value="{{ schedule.guide_date }}" placeholder="TUESDAY • JUNE 17, 2026">
        </div>

        <!-- VHF CHANNELS -->
        <div class="section">
            <h2>VHF Channels</h2>
            {% for i, ch in enumerate(schedule.vhf) %}
            <div class="channel">
                <strong>Channel {{ i + 2 }}</strong><br>
                Name:<br>
                <input type="text" name="vhf_{{ i }}_name" value="{{ ch.name }}">
                Schedule:<br>
                <input type="text" name="vhf_{{ i }}_schedule" value="{{ ch.schedule }}">
            </div>
            {% endfor %}
        </div>

        <!-- UHF CHANNELS -->
        <div class="section">
            <h2>UHF Channels</h2>
            {% for i, ch in enumerate(schedule.uhf) %}
            <div class="channel">
                <strong>Channel {{ i + 2 }}</strong><br>
                Name:<br>
                <input type="text" name="uhf_{{ i }}_name" value="{{ ch.name }}">
                Schedule:<br>
                <input type="text" name="uhf_{{ i }}_schedule" value="{{ ch.schedule }}">

                {% if ch.content %}
                    Content Type:<br>
                    <input type="text" name="uhf_{{ i }}_content_type" value="{{ ch.content.type }}">
                    Content HTML:<br>
                    <textarea name="uhf_{{ i }}_content_html" rows="5">{{ ch.content.html }}</textarea>
                {% else %}
                    <em>No content</em><br>
                    Content Type:<br>
                    <input type="text" name="uhf_{{ i }}_content_type" value="">
                    Content HTML:<br>
                    <textarea name="uhf_{{ i }}_content_html" rows="5"></textarea>
                {% endif %}
            </div>
            {% endfor %}
        </div>

        <button type="button" onclick="saveAllChanges()">Save All Changes</button>
    </form>

    <script>
        async function saveAllChanges() {
            const form = document.getElementById('adminForm');
            const formData = new FormData(form);
            const password = new URLSearchParams(window.location.search).get('password') || '';

            const newSchedule = {
                guide_date: formData.get('guide_date'),
                vhf: [],
                uhf: []
            };

            // Build VHF
            {% for i in range(schedule.vhf|length) %}
            newSchedule.vhf.push({
                id: "{{ schedule.vhf[i].id }}",
                name: formData.get('vhf_{{ i }}_name'),
                schedule: formData.get('vhf_{{ i }}_schedule')
            });
            {% endfor %}

            // Build UHF
            {% for i in range(schedule.uhf|length) %}
            const uhfItem = {
                id: "{{ schedule.uhf[i].id }}",
                name: formData.get('uhf_{{ i }}_name'),
                schedule: formData.get('uhf_{{ i }}_schedule')
            };

            const cType = formData.get('uhf_{{ i }}_content_type');
            const cHtml = formData.get('uhf_{{ i }}_content_html');
            if (cType && cHtml) {
                uhfItem.content = { type: cType, html: cHtml };
            }
            newSchedule.uhf.push(uhfItem);
            {% endfor %}

            const res = await fetch('/api/schedule/save?password=' + password, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newSchedule)
            });

            const result = await res.json();
            alert(result.message || "Saved!");
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)