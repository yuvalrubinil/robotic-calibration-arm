import argparse
import subprocess
from flask import Flask, jsonify, request

app = Flask(__name__)

latest_status = None


@app.route('/status', methods=['POST'])
def receive_status():
    global latest_status
    latest_status = request.get_json(force=True)
    return jsonify({"ok": True})

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json(force=True)
    program_name = data.get('program')
    
    if not program_name:
        return jsonify({"ok": False, "error": "No program name provided"}), 400

    print(f"Starting program: {program_name}")
    # Run the program asynchronously so we don't block the HTTP response
    try:
        subprocess.Popen(["python", "main.py", program_name])
        return jsonify({"ok": True, "message": f"Started {program_name}"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Arm Jetson HTTP receiver')
    parser.add_argument('--port', type=int, default=5001, help='Port to listen on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port, threaded=True)
    