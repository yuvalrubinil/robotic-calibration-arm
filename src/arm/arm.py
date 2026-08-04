import json
from adafruit_servokit import ServoKit

from servos.servo import Servo


class Arm:
    def __init__(self, servo_config):
        # init PCA9685
        self.kit = ServoKit(channels=16)

        # load servo_config
        with open(servo_config, "r") as f:
            config = json.load(f)

        type_configs = config["types"]

        self.servos = {}

        for channel_str, servo_cfg in config.items():
            if channel_str == "types":
                continue

            channel = int(channel_str)
            type_cfg = type_configs[servo_cfg["type"]]
            servo = Servo(
                kit=self.kit,
                channel=channel,
                name=servo_cfg["name"],
                type=servo_cfg["type"],
                logical_zero=servo_cfg["logical_zero"],
                operating_range=tuple(servo_cfg["operating_range"]),
                servo_range=type_cfg["range"],
                min_pulse=type_cfg["min_pulse"],
                max_pulse=type_cfg["max_pulse"])

            self.servos[servo.name] = servo

    def set_angle_config(self, angle_config):
        """
        Set multiple servo angles.

        Example:
        {
            "base": 0,
            "shoulder": 45,
            "elbow": -30
        }
        """
        for name, angle in angle_config.items():
            if name not in self.servos:
                raise KeyError(f"Unknown servo: '{name}'")

            self.servos[name].set_angle(angle)

    def center(self):
        """Move every servo to its logical zero position."""
        for servo in self.servos.values():
            servo.set_angle(0)