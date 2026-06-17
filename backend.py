 ==================== ADMIN PAGE HTML ====================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Retro TV Admin</title>
    <style>
        body { font-family: Arial, sans-serif; background: #111; color: #eee; padding: 20px; }
        h1 { color: #0ff; }
        .channel { background: #222; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; background: #333; color: #fff; border: 1px solid #555; }
        button { background: #0ff; color: #000; padding: 12px 24px; font-size: 16px; border: none; cursor: pointer; margin-top: 20px; }
        button:hover { background: #0cc; }
        .section { margin-bottom: 40px; }
    </style>
</head>
<body>
    <h1>Retro TV Admin Panel</h1>
    <p>Edit your VHF and UHF channels below. Click Save when done.</p>

    <form id="adminForm">
        <div class="section">
            <h2>VHF Channels</h2>
            {% for i, ch in enumerate(schedule.vhf) %}
            <div class="channel">
                <strong>Channel {{ i + 2 }}</strong><br>
                Name: <input type="text" name="vhf_{{ i }}_name" value="{{ ch.name }}"><br>
                Schedule: <input type="text" name="vhf_{{ i }}_schedule" value="{{ ch.schedule }}"><br>
            </div>
            {% endfor %}
        </div>

        <div class="section">
            <h2>UHF Channels</h2>
            {% for i, ch in enumerate(schedule.uhf) %}
            <div class="channel">
                <strong>Channel {{ i + 2 }}</strong><br>
                Name: <input type="text" name="uhf_{{ i }}_name" value="{{ ch.name }}"><br>
                Schedule: <input type="text" name="uhf_{{ i }}_schedule" value="{{ ch.schedule }}"><br>

                {% if ch.content %}
                    Content Type: <input type="text" name="uhf_{{ i }}_content_type" value="{{ ch.content.type }}"><br>
                    Embed / Text HTML:<br>
                    <textarea name="uhf_{{ i }}_content_html" rows="4">{{ ch.content.html }}</textarea>
                {% else %}
                    <em>No content set</em><br>
                    Content Type: <input type="text" name="uhf_{{ i }}_content_type" value=""><br>
                    Embed / Text HTML:<br>
                    <textarea name="uhf_{{ i }}_content_html" rows="4"></textarea>
                {% endif %}
            </div>
            {% endfor %}
        </div>

        <button type="button" onclick="saveChanges()">Save Changes</button>
    </form>

    <script>
        async function saveChanges() {
            const form = document.getElementById('adminForm');
            const formData = new FormData(form);
            
            // Build the new schedule object
            const newSchedule = {