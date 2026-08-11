class Servo:

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

            # validate operating range
            physical_min = self.logical_zero + self.operating_range[0]
            physical_max = self.logical_zero + self.operating_range[1]
            if physical_min < 0 or self.servo_range < physical_max:
                raise ValueError(
                    f"{self.name}: operating range {self.operating_range} "
                    f"with logical_zero={self.logical_zero} exceeds "
                    f"physical range [0, {self.servo_range}]"
                )
            
            self.angle = 0

    def set_angle(self, angle):
        min_angle, max_angle = self.operating_range

        if not (min_angle <= angle <= max_angle):
            raise ValueError(
                f"{self.name}: angle {angle} outside operating range "
                f"{self.operating_range}"
            )
        
        physical_angle = self.logical_zero + angle
        self.kit.servo[self.channel].angle = physical_angle
        self.angle = angle

        