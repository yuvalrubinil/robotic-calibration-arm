class Servo:
    def __init__(self, kit, channel, servo_config):
        self.channel = channel
        self.name = servo_config["name"]
        self.type = servo_config["type"]
        self.logical_zero = servo_config["logical_zero"]
        self.operating_range = tuple(servo_config["operating_range"])
        self.position = servo_config.get("position")

        type_config = servo_config["type_config"]
        self.servo_range = type_config["range"]
        self.min_pulse = type_config["min_pulse"]
        self.max_pulse = type_config["max_pulse"]


        self.kit = kit
        hw = self.kit.servo[channel]
        hw.set_pulse_width_range(self.min_pulse, self.max_pulse)
        hw.actuation_range = self.servo_range

        self.angle = None

    def set_angle(self, angle):
        self.kit.servo[self.channel].angle = angle
        self.angle = angle

        