import requests
import threading

ARM_JETSON_IP = "192.168.1.240"
ARM_JETSON_PORT = 5001
REQUEST_TIMEOUT = 2  # sec

BASE_URL = "http://{}:{}".format(ARM_JETSON_IP, ARM_JETSON_PORT)


def _post_status(payload):
    try:
        requests.post(BASE_URL + "/status", json=payload, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        print("Failed to send status to arm Jetson: " + str(e))

# threaded post status
def post_status(payload):
    threading.Thread(target=_post_status, args=(payload,), daemon=True).start()


def send_frame_status(found, cover, corners_count):
    post_status({
        "type": "frame",
        "found": found,
        "cover": cover,
        "corners_count": corners_count,
    })


def send_calibration_done(success, calib_error):
    post_status({
        "type": "calibration_done",
        "success": success,
        "calib_error": calib_error,
    })

