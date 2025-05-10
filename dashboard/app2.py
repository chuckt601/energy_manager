from flask import Flask, jsonify, render_template

app = Flask(__name__)

dashboard_data = {
    "can_speed": 0,
    "charger_status": "unknown"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    return jsonify(dashboard_data)

def run_dashboard(host="0.0.0.0", port=5000):
    app.run(host=host, port=port, debug=False, use_reloader=False)
