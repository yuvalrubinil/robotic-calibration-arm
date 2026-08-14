import argparse
from arm import Arm
from pathlib import Path

ARM_CONFIG = Path(__file__).parent / "config.json"

parser = argparse.ArgumentParser(description="Run a calibration program on the arm.")
parser.add_argument("program", help="Name of the calibration program, saved as calibration_programs/<program_name>")
args = parser.parse_args()

arm = Arm(ARM_CONFIG)
arm.compile_program(args.program)
arm.execude()
