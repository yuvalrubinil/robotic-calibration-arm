import argparse
from flask import Flask, jsonify, request

app = Flask(__name__)

latest_status = None


@app.route('/status', methods=['POST'])
def receive_status():
    global latest_status
    latest_status = request.get_json(force=True)
    return jsonify({"ok": True})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Arm Jetson HTTP receiver')
    parser.add_argument('--port', type=int, default=5001, help='Port to listen on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port, threaded=True)
    