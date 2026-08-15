import os
import requests
import threading

ARM_JETSON_IP = "192.168.1.240"
ARM_JETSON_PORT = 5001
REQUEST_TIMEOUT = 2  # sec

BASE_URL = "http://{}:{}".format(ARM_JETSON_IP, ARM_JETSON_PORT)


def _post(path, error_label, **kwargs):
    try:
        response = requests.post(BASE_URL + path, timeout=REQUEST_TIMEOUT, **kwargs)
        response.raise_for_status()
        return True
    except (requests.RequestException, OSError) as e:
        print("Failed to send {} to arm Jetson: {}".format(error_label, e))
        return False


# threaded post
def _post_async(path, error_label, **kwargs):
    threading.Thread(target=_post, args=(path, error_label), kwargs=kwargs, daemon=True).start()


def send_frame_status(found, cover, corners_count):
    _post_async("/status", "status", json={
        "type": "frame",
        "found": found,
        "cover": cover,
        "corners_count": corners_count,
    })


def send_calibration_done(success, calib_error):
    _post_async("/status", "status", json={
        "type": "calibration_done",
        "success": success,
        "calib_error": calib_error,
    })


def send_calibration_program(program_path):
    try:
        with open(program_path, "rb") as f:
            filename = os.path.basename(program_path)
            data = f.read()
    except OSError as e:
        print("Failed to send calibration program to arm Jetson: " + str(e))
        return
    _post_async("/calibration_program", "calibration program", files={"file": (filename, data)})


def send_start(program_name):
    """Tell the arm Jetson to start running the named calibration program."""
    _post_async("/start", "start command", json={"program_name": program_name})
