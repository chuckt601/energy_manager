from flask import Flask, jsonify, render_template
import threading

def run_dashboard(can_data, wallbox_data):
     #app = Flask(__name__)
     app = Flask(__name__, template_folder="templates")

     #print("did it ever get to dashboard")

     @app.route("/")
     def index():
         #print("did it ever get to slash")
         return render_template("index.html")  # Looks in ./templates/index.html
    
     @app.route("/status")
     def status():
         #print("did it ever get to status")
         #print("CAN:", can_data)
         #print("Wallbox:", wallbox_data)

         return jsonify({
             "can": dict(can_data),
             "wallbox": dict(wallbox_data)
             })
   
     app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

     #def flask_thread():
     #   try:
     #        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
     #   except Exception as e:
     #         print("[dashboard] Flask thread crashed with exception:")
     #         traceback.print_exc()

     #try:
     #    thread = threading.Thread(target=flask_thread)
     #    thread.daemon = True
     #    thread.start()
     #    print("[dashboard] Flask server started on port 5000.")   

     #except Exception as e:
     #      print("[dashboard] Flask server failed to start")   
     #      traceback.print_exc()
 

