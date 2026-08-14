import sys
import time
from adafruit_servokit import ServoKit

DS3218_CHANNELS = {0, 1, 2, 3}
MG996R_CHANNELS = {4, 5}
ALL_CHANNELS = DS3218_CHANNELS | MG996R_CHANNELS


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
    print("  <channel> <angle>   Move servo")
    print("  reset               Move arm to resting position")
    print("  exit                Quit")
    print()


def reset(kit):
    kit.servo[0].angle = 140
    kit.servo[1].angle = 270
    kit.servo[2].angle = 200
    kit.servo[3].angle = 100
    kit.servo[4].angle = 90
    kit.servo[5].angle = 90
    time.sleep(1)
    release_all(kit)

def main():
    try:
        kit = ServoKit(channels=16)
        configure_servos(kit)
    except Exception as e:
        print(f"Failed to initialize ServoKit: {e}")
        sys.exit(1)

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
    