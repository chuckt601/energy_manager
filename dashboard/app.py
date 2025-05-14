from flask import Flask, jsonify, render_template, request
import threading

def run_dashboard(can_data, wallbox_data, mode,logger):    
     app = Flask(__name__, template_folder="templates")     

     @app.route("/")
     def index():         
         return render_template("index.html")  # Looks in ./templates/index.html
    
     @app.route("/status")
     def status():
         logger.info("Received /status request")
         return jsonify({
             "can": dict(can_data),
             "wallbox": dict(wallbox_data)
             })
     @app.route("/set_mode", methods=["POST"])
     def set_mode():
         logger.info("Received /set mode request")
         new_mode = request.json.get("mode")
         if new_mode:
             mode.value = new_mode
             #logger.info(f"Charging mode set to: {new_mode}")
             return jsonify({"status": "success", "mode": mode.value})
         return jsonify({"status": "error", "message": "Invalid mode"}), 400

     @app.route("/get_mode")
     def get_mode():
         logger.info("Received /get mode request")
         return jsonify({"mode": mode.value})        
   
     app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

    
 

