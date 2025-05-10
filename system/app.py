from flask import Flask, render_template, jsonify
import random  # Replace this with real sensor or Wallbox data

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def get_status():
    # Dummy data for now. Replace with real values later.
    return jsonify({
        "charger_status": "Charging",
        "current_amp": random.randint(10, 32),
        "voltage": 230
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
