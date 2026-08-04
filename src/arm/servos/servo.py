class Servo:

    def __init__(self, kit, channel, name, type, logical_zero, operating_range, servo_range, min_pulse, max_pulse):
        self.kit = kit
        self.channel = channel
        self.name = name
        self.type = type

        self.logical_zero = logical_zero
        self.operating_range = tuple(operating_range)
        self.servo_range = servo_range

        hw = self.kit.servo[channel]
        hw.set_pulse_width_range(min_pulse, max_pulse)
        hw.actuation_range = servo_range

        # validate operating range fits within the servo physical capabilities
        physical_min = logical_zero + self.operating_range[0]
        physical_max = logical_zero + self.operating_range[1]
        if physical_min < 0 or servo_range < physical_max:
            raise ValueError(
                f"{name}: operating range {self.operating_range} with "
                f"logical_zero={logical_zero} exceeds physical range "
                f"[0, {servo_range}]"
            )

        self.angle = 0

    def set_angle(self, logical_angle):
        min_angle, max_angle = self.operating_range

        if not (min_angle <= logical_angle <= max_angle):
            raise ValueError(
                f"{self.name}: angle {logical_angle} outside operating range "
                f"{self.operating_range}"
            )
        
        physical_angle = self.logical_zero + logical_angle
        self.kit.servo[self.channel].angle = physical_angle
        self.angle = logical_angle

        