import time
from adafruit_servokit import ServoKit

CHANNEL = 0   

kit = ServoKit(channels=16)

servo = kit.servo[CHANNEL]

# MG996R 180° calibration
servo.set_pulse_width_range(1000, 2000)
servo.actuation_range = 180

print(f"Centering MG996R on channel {CHANNEL}...")

servo.angle = 90

time.sleep(3)

print("MG996R centered.")