from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "App is running!"

@app.route('/api/schedule')
def get_schedule():
    return jsonify({"message": "API is working"})

@app.route('/test')
def test():
    return "Test route is working!"

@app.route('/admin')
def admin():
    return "Admin route is working!"

if __name__ == '__main__':
    app.run(debug=True, port=5000)