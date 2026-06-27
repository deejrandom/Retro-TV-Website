from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os

app = Flask(__name__)
CORS(app)
app.secret_key = "RetroTV_SuperSecretKey_2026_XYZ123"

ADMIN_PASSWORD = "MuffinBennett!987"
SCHEDULE_FILE = "schedule.json"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# =====================
# DEFAULT SCHEDULE (This is your full site data)
# =====================
DEFAULT_SCHEDULE = {
    "guide_scroll_speed": 0.36,
    "vhf": [
        {"id": "home", "name": "HOME", "schedule": "Welcome to Warren C. Bennett's Retro Future", "presentation": "single", "media": []},
        {"id": "writing", "name": "WRITING", "schedule": "Random Encounters", "presentation": "single", "media": []},
        {"id": "games", "name": "GAMES", "schedule": "Retro gaming hub", "presentation": "single", "media": []},
        {
            "id": "pixelart",
            "name": "PIXEL ART",
            "schedule": "Pixel Art Galleries",
            "presentation": "gallery",
            "media": [
                {"title": "Final Fantasy Logo", "type": "image", "url": "https://warrencbennett.com/retro-tv/ff-Logo-NES.webp", "gallery_group": "Final Fantasy", "is_group_cover": True},
                {"title": "Black Mage", "type": "image", "url": "https://warrencbennett.com/retro-tv/black-mage-nes.png", "gallery_group": "Final Fantasy"},
                {"title": "Red Mage", "type": "image", "url": "https://warrencbennett.com/retro-tv/redmage-nes.png", "gallery_group": "Final Fantasy"},
                {"title": "White Mage", "type": "image", "url": "https://warrencbennett.com/retro-tv/white-mage-nes.png", "gallery_group": "Final Fantasy"}
            ]
        },
        {"id": "films", "name": "FILMS", "schedule": "Film related content", "presentation": "single", "media": []},
        {"id": "tv", "name": "TV", "schedule": "TV related content", "presentation": "single", "media": []},
        {"id": "where", "name": "WHERE CAN YOU FIND ME?", "schedule": "Social links", "presentation": "single", "media": []}
    ],
    "uhf": [
        {"id": "uhf1", "name": "CARTOONS", "schedule": "Public Domain Cartoons", "presentation": "single", "media": []},
        {"id": "uhf2", "name": "CARTOONS", "schedule": "More Public Domain Cartoons", "presentation": "single", "media": []},
        {"id": "uhf3", "name": "TV SHOWS", "schedule": "Classic Public Domain TV", "presentation": "single", "media": []},
        {"id": "uhf4", "name": "TV SHOWS", "schedule": "More Classic TV", "presentation": "single", "media": []},
        {
            "id": "uhf5",
            "name": "FILMS",
            "schedule": "Double Indemnity - All day",
            "presentation": "single",
            "media": [
                {"title": "Double Indemnity (1944)", "type": "youtube", "url": "https://www.youtube.com/watch?v=wI5xaum_HlA"}
            ]
        },
        {"id": "uhf6", "name": "FILMS", "schedule": "More Public Domain Films", "presentation": "single", "media": []}
    ]
}

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            data = json.load(f)
            # Make sure it has the new structure
            if "vhf" not in data:
                data = DEFAULT_SCHEDULE
            return data
    return DEFAULT_SCHEDULE

def save_schedule(data):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)

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

# =====================
# ADMIN + LOGIN (simplified for now)
# =====================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body style="background:#111; color:#39ff14; font-family: monospace; padding:40px;">
    <h2>Retro TV Admin Login</h2>
    <form method="POST">
        <input type="password" name="password" placeholder="Password" style="padding:10px; font-size:18px;">
        <button type="submit" style="padding:10px 20px; font-size:18px;">Login</button>
    </form>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            user = User("admin")
            login_user(user)
            return redirect('/admin')
        return "Invalid password", 401
    return render_template_string(LOGIN_HTML)

@app.route('/admin')
@login_required
def admin():
    return "Admin panel is working. You can now use it to add/edit channels."

if __name__ == '__main__':
    app.run(debug=True)