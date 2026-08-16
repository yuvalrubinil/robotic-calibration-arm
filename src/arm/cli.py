import json
import sys
import time
from pathlib import Path
from adafruit_servokit import ServoKit
from ik_compiler import IKCompiler

CONFIG_PATH = Path(__file__).parent / "config.json"

DS3218_CHANNELS = {0, 1, 2, 3}
MG996R_CHANNELS = {4, 5}
ALL_CHANNELS = DS3218_CHANNELS | MG996R_CHANNELS

SERVO_NAMES = ("base", "shoulder", "elbow", "wrist", "yaw", "roll")


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def load_zero_state():
    return load_config()["arm"]["zero_state"]


def configure_servos(kit):
    for ch in DS3218_CHANNELS:
        kit.servo[ch].set_pulse_width_range(500, 2500)
        kit.servo[ch].actuation_range = 270

    for ch in MG996R_CHANNELS:
        kit.servo[ch].set_pulse_width_range(500, 2500)
        kit.servo[ch].actuation_range = 180


def max_angle(channel):
    if channel in DS3218_CHANNELS:
        return 270
    if channel in MG996R_CHANNELS:
        return 180
    raise ValueError(f"Invalid channel: {channel}")


def release_all(kit):
    for ch in ALL_CHANNELS:
        kit.servo[ch].angle = None
    print("All servos released.")


def print_help():
    print("\nCommands:")
    print("  <channel> <angle>          Move servo")
    print("  r <r> a <a> h <h> [ro <ro>]  Solve target with IK and move arm")
    print("  reset                      Move arm to resting position")
    print("  exit                       Quit")
    print()


def reset(kit):
    for channel, angle in enumerate(load_zero_state()):
        kit.servo[channel].angle = angle
    time.sleep(1)
    release_all(kit)


def run_ik_line(kit, ikc, line):
    tokens = line.split()
    if len(tokens) % 2 != 0:
        raise ValueError(f"Malformed line: {line!r}")

    point = dict(zip(tokens[0::2], tokens[1::2]))
    missing_keys = {"r", "a", "h"} - point.keys()
    if missing_keys:
        raise ValueError(f"Missing {sorted(missing_keys)}: {line!r}")

    r, theta, h = float(point["r"]), float(point["a"]), float(point["h"])
    roll_angle = float(point["ro"]) if "ro" in point else 0

    angle_config = ikc.calc_angle_config(r, theta, h, roll_angle=roll_angle)
    servo_angles = ikc.to_servo_angels(angle_config)

    for channel, angle in enumerate(servo_angles):
        kit.servo[channel].angle = angle
    time.sleep(1)

    print(f"Executed -> {dict(zip(SERVO_NAMES, servo_angles))}")


def main():
    try:
        kit = ServoKit(channels=16)
        configure_servos(kit)
    except Exception as e:
        print(f"Failed to initialize ServoKit: {e}")
        sys.exit(1)

    ikc = IKCompiler(load_config())

    print_help()

    while True:
        try:
            line = input("> ").strip()

            if not line:
                continue

            cmd = line.lower()

            if cmd in ("exit", "quit"):
                break

            if cmd == "reset":
                reset(kit)
                continue

            parts = line.split()

            if parts[0].lower() == "r":
                run_ik_line(kit, ikc, line)
                continue

            if len(parts) != 2:
                print("Usage: <channel> <angle>")
                continue

            channel = int(parts[0])
            angle = float(parts[1])

            limit = max_angle(channel)

            if not (0 <= angle <= limit):
                print(f"Angle must be between 0 and {limit}")
                continue

            kit.servo[channel].angle = angle
            print(f"Servo {channel} -> {angle}°")

        except ValueError as e:
            print(e)
        except KeyboardInterrupt:
            print()
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
    