import argparse
import multiprocessing
import time
from pathlib import Path

from flask import Flask, jsonify, request

from arm import Arm

ARM_CONFIG = Path(__file__).parent / "config.json"
CALIBRATION_PROGRAMS_DIR = Path(__file__).parent / "calibration_programs"

STATUS_TIMEOUT_SECONDS = 10
STATUS_POLL_INTERVAL_SECONDS = 0.2

app = Flask(__name__)

arm = Arm(ARM_CONFIG)
run_process = None

status_manager = multiprocessing.Manager()
shared_status = status_manager.dict(value=None)


def wait_board_found(shared_status, timeout=STATUS_TIMEOUT_SECONDS):
    shared_status["value"] = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = shared_status["value"]
        if status is not None:
            if status.get("type") == "frame" and status.get("found"): # found the board
                return
            shared_status["value"] = None  
        time.sleep(STATUS_POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"Status not received within {timeout}s")


def run_program(program_name, side, shared_status):
    arm.ikc.set_lens(side)

    def step():
        wait_board_found(shared_status)

    try:
        arm.compile_program(program_name)
        arm.execute(step=step)
    except TimeoutError as e:
        print(f"Aborting program: {e}")
        arm.reset()


@app.route('/status', methods=['POST'])
def receive_status():
    shared_status["value"] = request.get_json(force=True)
    return jsonify({"ok": True})


@app.route('/calibration_program', methods=['POST'])
def upload_calibration_program():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "No file provided"}), 400

    CALIBRATION_PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    file.save(CALIBRATION_PROGRAMS_DIR / file.filename)
    return jsonify({"ok": True})


@app.route('/start', methods=['POST'])
def start():
    global run_process

    data = request.get_json(force=True)
    program_name = data.get('program_name')
    side = data.get('side')

    if not program_name:
        return jsonify({"ok": False, "error": "No program name provided"}), 400

    if side not in ("left", "right"):
        return jsonify({"ok": False, "error": "side must be 'left' or 'right'"}), 400

    # Lock the server: refuse a new run while one is already in progress.
    if run_process is not None and run_process.is_alive():
        return jsonify({"ok": False, "error": "Arm is busy running a program"}), 409

    print(f"Starting program: {program_name} ({side} lens)")
    # Run in a separate process so the Flask server keeps responding to
    # other requests (e.g. /status) while the arm is moving.
    run_process = multiprocessing.Process(target=run_program, args=(program_name, side, shared_status), daemon=True)
    run_process.start()
    return jsonify({"ok": True, "message": f"Started {program_name}"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Arm Jetson HTTP receiver')
    parser.add_argument('--port', type=int, default=5001, help='Port to listen on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port, threaded=True)
