import argparse
from arm import Arm
from pathlib import Path
import threading
from calibration_arm_server import app as status_app

threading.Thread(
    target=status_app.run,
    kwargs={"host": "0.0.0.0", "port": 5001, "threaded": True, "use_reloader": False},
    daemon=True,
).start()

ARM_CONFIG = Path(__file__).parent / "config.json"

parser = argparse.ArgumentParser(description="Run a calibration program on the arm.")
parser.add_argument("program", help="Name of the calibration program, saved as calibration_programs/<program_name>")
args = parser.parse_args()

arm = Arm(ARM_CONFIG)
arm.compile_program(args.program)
arm.execute()
