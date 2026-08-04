import json
import math
import os

class KinematicsCompiler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KinematicsCompiler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, lengths_file=None):
        if getattr(self, '_initialized', False):
            return
        
        if lengths_file is None:
            # Default to the lenghts.json in the parent directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            lengths_file = os.path.join(base_dir, "lenghts.json")
            
        with open(lengths_file, "r") as f:
            self.lengths = json.load(f)
            
        self._initialized = True

    def calculate_ik(self, radius, theta, height):
        """
        Calculate Inverse Kinematics for motors 0, 1, 2, 3.
        
        :param radius: Radius from the lens (planar distance)
        :param theta: Angle from the lens in degrees (base angle)
        :param height: Height from the lens
        :return: Dictionary mapping motor number to angle in degrees.
        """
        L1 = self.lengths.get("shoulder_arm", 0)
        L2 = self.lengths.get("elbow_arm", 0)
        L3 = self.lengths.get("wrist_arm", 0)
        
        # If lengths are 0 (not measured yet), we can't compute IK properly.
        # Returning base angle and 0 for others to avoid math domain errors.
        if L1 == 0 or L2 == 0:
            return {0: theta, 1: 0, 2: 0, 3: 0}

        # The wrist must always be normal to the ground (pointing straight down)
        phi = math.radians(-90)

        # 1. Base angle is simply theta
        theta0 = theta

        # 2. The input (radius, height) is already the position of the wrist top (wrist joint)
        R_w = radius
        Z_w = height

        # 3. Calculate distance from shoulder to wrist joint
        D = math.sqrt(R_w**2 + Z_w**2)

        # Check if the target is reachable by the 2-link arm (shoulder + elbow)
        if D > (L1 + L2):
            # Target is too far, stretch arm fully towards the target
            D = L1 + L2
        elif D < abs(L1 - L2):
            # Target is too close
            D = abs(L1 - L2)

        # 4. Law of cosines for shoulder angle (theta1)
        # alpha is the angle between the shoulder-to-wrist line and the shoulder link
        cos_alpha = (L1**2 + D**2 - L2**2) / (2 * L1 * D)
        # Clamp to avoid floating point issues
        cos_alpha = max(-1.0, min(1.0, cos_alpha))
        alpha = math.acos(cos_alpha)
        
        # gamma is the angle of the shoulder-to-wrist line from horizontal
        gamma = math.atan2(Z_w, R_w)
        
        # Shoulder angle (elbow down configuration)
        theta1 = gamma + alpha

        # 5. Law of cosines for elbow angle (theta2)
        # beta is the inner angle of the elbow joint
        cos_beta = (L1**2 + L2**2 - D**2) / (2 * L1 * L2)
        cos_beta = max(-1.0, min(1.0, cos_beta))
        beta = math.acos(cos_beta)
        
        # Elbow angle relative to shoulder link (negative for elbow down)
        theta2 = beta - math.pi

        # 6. Calculate wrist angle (theta3) to maintain the desired phi
        # The sum of angles theta1 + theta2 + theta3 = phi
        theta3 = phi - theta1 - theta2

        # Convert back to degrees
        return {
            0: theta0,
            1: math.degrees(theta1),
            2: math.degrees(theta2),
            3: math.degrees(theta3)
        }

    def compile_from_file(self, input_filepath, output_filepath):
        """
        Reads a text file containing targets formatted as (radius, theta, height).
        Computes the inverse kinematics for each line and writes the results to an output file.
        """
        with open(input_filepath, 'r') as infile, open(output_filepath, 'w') as outfile:
            for line in infile:
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
                        
                        # Calculate IK
                        ik_result = self.calculate_ik(radius, theta, height)
                        
                        # Write result dictionary to file
                        outfile.write(f"{ik_result}\n")
                    except ValueError:
                        outfile.write(f"Error processing values: {line}\n")
                else:
                    outfile.write(f"Invalid format (expected 3 values): {line}\n")
