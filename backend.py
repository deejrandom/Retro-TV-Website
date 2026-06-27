from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

SCHEDULE_FILE = 'schedule.json'

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    # Fallback data
    return {
        "vhf": [
            {"id": "home", "name": "HOME", "schedule": "Welcome message"},
            {"id": "writing", "name": "WRITING", "schedule": "Random Encounters"},
            {"id": "games", "name": "GAMES", "schedule": "Retro gaming hub"},
            {"id": "pixelart", "name": "PIXEL ART", "schedule": "Pixel Art Galleries"},
            {"id": "films", "name": "FILMS", "schedule": "Film related content"},
            {"id": "tv", "name": "TV", "schedule": "TV related content"},
            {"id": "where", "name": "WHERE CAN YOU FIND ME?", "schedule": "Social links"}
        ],
        "uhf": [
            {"id": "uhf1", "name": "CARTOONS", "schedule": "Public Domain Cartoons"},
            {"id": "uhf2", "name": "CARTOONS", "schedule": "More Public Domain Cartoons"},
            {"id": "uhf3", "name": "TV SHOWS", "schedule": "Classic Public Domain TV"},
            {"id": "uhf4", "name": "TV SHOWS", "schedule": "More Classic TV"},
            {"id": "uhf5", "name": "FILMS", "schedule": "Double Indemnity - All day"},
            {"id": "uhf6", "name": "FILMS", "schedule": "More Public Domain Films"}
        ]
    }

def save_schedule(data):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)

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

@app.route('/')
def home():
    return "Backend is running"

if __name__ == '__main__':
    app.run(debug=True)