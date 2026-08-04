import sys
from adafruit_servokit import ServoKit


# Servo channel groups
DS3218_CHANNELS = {0, 1, 2, 3}
MG996R_CHANNELS = {4, 5}


def configure_servos(kit):
    """Configure each servo according to its type."""

    # DS3218 (270°)
    for ch in DS3218_CHANNELS:
        kit.servo[ch].set_pulse_width_range(500, 2500)
        kit.servo[ch].actuation_range = 270

    # MG996R (180°)
    for ch in MG996R_CHANNELS:
        kit.servo[ch].set_pulse_width_range(500, 2500)
        kit.servo[ch].actuation_range = 180


def max_angle(channel):
    """Return the maximum valid angle for a channel."""

    if channel in DS3218_CHANNELS:
        return 270

    if channel in MG996R_CHANNELS:
        return 180

    raise ValueError(f"Channel {channel} is not configured.")


def main():
    try:
        kit = ServoKit(channels=16)
        configure_servos(kit)
    except Exception as e:
        print(f"Failed to initialize ServoKit: {e}")
        sys.exit(1)

    print("Commands:")
    print("  <channel> <angle>")
    print()
    print("Channels:")
    print("  0-3 : DS3218 (0-270°)")
    print("  4-5 : MG996R (0-180°)")
    print()
    print("Type 'exit' to quit.")

    while True:
        try:
            line = input("servo$ ").strip()

            if line.lower() in ("exit", "quit"):
                break

            channel_str, angle_str = line.split()

            channel = int(channel_str)
            angle = float(angle_str)

            limit = max_angle(channel)

            if not (0 <= angle <= limit):
                print(f"Angle must be between 0 and {limit}°.")
                continue

            kit.servo[channel].angle = angle

            print(f"Channel {channel} -> {angle}°")

        except ValueError as e:
            print(e)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
    