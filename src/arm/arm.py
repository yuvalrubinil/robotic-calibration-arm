import json
import time
from pathlib import Path
from adafruit_servokit import ServoKit
from arm.servo import Servo
from ik_compiler import IKCompiler

CALIBRATION_PROGRAMS_DIR = Path(__file__).parent / "calibration_programs"


class Arm:
    def __init__(self, arm_config):
        # init PCA9685
        self.kit = ServoKit(channels=16)

        # load arm_config
        with open(arm_config, "r") as f:
            config = json.load(f)

        # init the inverse kinematics compiler
        self.ikc = IKCompiler(config)

        # init servos
        servo_config = config["arm"]["servos"]
        self.servos = []
        for channel_str, _ in servo_config.items():
            if channel_str == "types":
                continue

            channel = int(channel_str)
            servo = Servo(
                kit=self.kit,
                channel=channel,
                servo_config=servo_config[channel]
            )
            self.servos.append(servo)

    def set_angle_config(self, angle_config):
        for idx, angle in enumerate(angle_config):
            self.servos[idx].set_angle(angle)
        time.sleep(1)

    def compile_program(self, program_name):
        program_path = CALIBRATION_PROGRAMS_DIR / program_name
        return self.ikc.compile(program_path)

    def execute(self, calibration_program):
        for angle_config in calibration_program:
            self.set_angle_config(angle_config)
            
