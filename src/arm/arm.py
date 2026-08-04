import json
from adafruit_servokit import ServoKit

import time
from kinematics_compiler.kinematics_compiler import KinematicsCompiler
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

    def execute_from_file(self, file_path, delay=1.0):
        """
        Reads a text file containing targets formatted as (radius, theta, height).
        Computes the inverse kinematics for each line and sets the arm servos to those angles.
        Pauses for `delay` seconds between each movement.
        """
        compiler = KinematicsCompiler()
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Strip parentheses and split by comma
                clean_line = line.replace('(', '').replace(')', '')
                parts = clean_line.split(',')
                
                if len(parts) == 3:
                    try:
                        radius = float(parts[0].strip())
                        theta = float(parts[1].strip())
                        height = float(parts[2].strip())
                        
                        # Calculate IK (returns dict mapping 0->base, 1->shoulder, etc.)
                        ik_result = compiler.calculate_ik(radius, theta, height)
                        
                        # Map numerical motor indices to string names
                        angle_config = {
                            "base": ik_result.get(0, 0),
                            "shoulder": ik_result.get(1, 0),
                            "elbow": ik_result.get(2, 0),
                            "wrist": ik_result.get(3, 0)
                        }
                        
                        print(f"Moving to (r={radius}, th={theta}, h={height}) -> {angle_config}")
                        self.set_angle_config(angle_config)
                        
                        # Wait for the arm to finish moving before processing the next line
                        time.sleep(delay)
                        
                    except ValueError:
                        print(f"Error processing values, skipping: {line}")
                else:
                    print(f"Invalid format, skipping: {line}")