import time
from adafruit_servokit import ServoKit

CHANNEL = 0   

kit = ServoKit(channels=16)

servo = kit.servo[CHANNEL]

# DS3218 270° calibration
servo.set_pulse_width_range(500, 2500)
servo.actuation_range = 270

print(f"Centering DS3218 on channel {CHANNEL}...")

servo.angle = 135

time.sleep(3)

print("DS3218 centered.")