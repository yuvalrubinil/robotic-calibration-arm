import json
#from adafruit_servokit import ServoKit
#from arm.servo import Servo


class Arm:
    def __init__(self, arm_config):
        # init PCA9685
        #self.kit = ServoKit(channels=16)

        # load arm_config
        with open(arm_config, "r") as f:
            config = json.load(f)

        # init servos
        servo_config = config["arm"]["servos"]
        self.servos = {}
        for channel_str, _ in servo_config.items():
            if channel_str == "types":
                continue

            channel = int(channel_str)
            servo = Servo(
                kit=self.kit,
                channel=channel,
                servo_config=servo_config[channel]
            )

            self.servos[servo.name] = servo


    def set_angle_config(self, angle_config):
        for name, angle in angle_config.items():
            self.servos[name].set_angle(angle)

