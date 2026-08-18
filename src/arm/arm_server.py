import argparse
import multiprocessing
import time
from pathlib import Path

from flask import Flask, jsonify, request

from arm import Arm
from arm_director import ArmDirector

ARM_CONFIG = Path(__file__).parent / "config.json"

STATUS_TIMEOUT_SECONDS = 10
STATUS_POLL_INTERVAL_SECONDS = 0.2

app = Flask(__name__)

arm = Arm(ARM_CONFIG)
arm_process = None

status_manager = multiprocessing.Manager()
shared_status = status_manager.dict(value=None)


def wait_frame_status(shared_status, timeout=STATUS_TIMEOUT_SECONDS):
    shared_status["value"] = None
    deadline = time.time() + timeout

    while time.time() < deadline:
        status = shared_status["value"]
        if status is not None and status.get("type") == "frame":
            return status
        time.sleep(STATUS_POLL_INTERVAL_SECONDS)
        
    raise TimeoutError(f"Status not received within {timeout}s")


def calibrate(side, shared_status):
    arm.ikc.set_lens(side)
    arm_director = ArmDirector()

    try:
        arm.reset()
        r, a, h = arm_director.first_position()
        while not arm_director.done:
            arm.move_to(r, a, h)

            status = wait_frame_status(shared_status)

            found, corners, frame_size, cover = status.get("found"), status.get("corners"), status.get("frame_size"), status.get("cover")
            r, a, h = arm_director.next_target(found, corners, frame_size, cover)

    except TimeoutError as e:
        print(f"Aborting calibration: {e}")
    finally:
        arm.reset()


@app.route('/status', methods=['POST'])
def receive_status():
    shared_status["value"] = request.get_json(force=True)
    return jsonify({"ok": True})


@app.route('/start', methods=['POST'])
def start():
    global arm_process

    data = request.get_json(force=True)
    side = data.get('side')

    if side not in ("left", "right"):
        return jsonify({"ok": False, "error": "side must be 'left' or 'right'"}), 400

    # lock the server
    if arm_process is not None and arm_process.is_alive():
        return jsonify({"ok": False, "error": "Arm is busy running the calibration walk"}), 409

    print(f"Starting smart calibration ({side} lens)")
    arm_process = multiprocessing.Process(target=calibrate, args=(side, shared_status), daemon=True)
    arm_process.start()
    return jsonify({"ok": True, "message": f"Started calibration ({side})"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Arm Jetson HTTP receiver')
    parser.add_argument('--port', type=int, default=5001, help='Port to listen on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port, threaded=True)
