import json
import time
from adafruit_servokit import ServoKit
from servo import Servo
from ik_compiler import IKCompiler


class Arm:
    def __init__(self, arm_config):
        # init PCA9685
        self.kit = ServoKit(channels=16)

        # load arm_config
        with open(arm_config, "r") as f:
            config = json.load(f)

        # init the inverse kinematics compiler
        self.ikc = IKCompiler(config)

        # resting position
        self.zero_state = config["arm"]["zero_state"]

        # init servos
        servo_config = config["arm"]["servos"]
        servo_types = servo_config["types"]
        self.servos = []
        for channel_str, _ in servo_config.items():
            if channel_str == "types":
                continue

            channel = int(channel_str)
            servo = Servo(
                kit=self.kit,
                channel=channel,
                servo_config={**servo_config[channel_str], "type_config": servo_types[servo_config[channel_str]["type"]]}
            )
            self.servos.append(servo)

    def set_angle_config(self, angle_config):
        for idx, angle in enumerate(angle_config):
            self.servos[idx].set_angle(angle)
        time.sleep(1)

    def reset(self):
        self.set_angle_config(self.zero_state)

    def move_to(self, r, theta, h, roll_angle=0):
        angle_config = self.ikc.calc_angle_config(r, theta, h, roll_angle=roll_angle)
        servo_angles = self.ikc.to_servo_angels(angle_config)
        self.set_angle_config(servo_angles)

