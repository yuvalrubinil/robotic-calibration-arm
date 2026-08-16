import math
import numpy as np
from lens import Lens

def rotate_vector(vector, angle_deg, axis):
    angle_rad = math.radians(angle_deg)

    if axis == "x": # tilt rotation
        R = np.array([
            [1, 0, 0],
            [0, np.cos(angle_rad), -np.sin(angle_rad)],
            [0, np.sin(angle_rad), np.cos(angle_rad)],
        ])
    elif axis == "y": # roll rotation
        R = np.array([
            [np.cos(angle_rad), 0, np.sin(angle_rad)],
            [0, 1, 0],
            [-np.sin(angle_rad), 0, np.cos(angle_rad)],
        ])
    else:  # yaw rotation
        R = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad), 0],
            [np.sin(angle_rad), np.cos(angle_rad), 0],
            [0, 0, 1],
        ])

    return R @ vector


class IKCompiler:
    def __init__(self, config):
        lengths = config["arm"]["lengths"]
        servos = config["arm"]["servos"]
        lenses = config["camera"]["lenses"]

        # yaw & roll arm lengths
        self.L1 = lengths["L1"]
        self.L2 = lengths["L2"]
        self.L3 = lengths["L3"]

        # arm lengths
        self.shoulder_arm_length = lengths["shoulder_arm"]
        self.elbow_arm_length = lengths["elbow_arm"]
        self.wrist_arm_length = lengths["wrist_arm"]

        # translation_vectors
        self.reset_translation_vectors()

        # camera lenses
        self.left_lens = Lens(lenses['left_lens'])
        self.right_lens = Lens(lenses['right_lens'])
        self.set_lens("right")

        # positions
        self.base_position = np.array(servos["0"]["position"], dtype=float)
        self.shoulder_servo_position = np.array(servos["1"]["position"], dtype=float)

        # logical zeros
        self.base_logical_zero = servos["0"]["logical_zero"]
        self.shoulder_logical_zero = servos["1"]["logical_zero"]
        self.elbow_logical_zero = servos["2"]["logical_zero"]
        self.wrist_logical_zero = servos["3"]["logical_zero"]
        self.yaw_logical_zero = servos["4"]["logical_zero"]
        self.roll_logical_zero = servos["5"]["logical_zero"]

        # operating ranges
        self.servo_operating_ranges = [(servos[str(i)]["name"], tuple(servos[str(i)]["operating_range"])) for i in range(6)]

    def set_lens(self, side):
        if side == "left":
            self.lens = self.left_lens
        elif side == "right":
            self.lens = self.right_lens
        else:
            raise ValueError(f"Unknown lens side: {side!r}, expected 'left' or 'right'")

    def reset_translation_vectors(self):
        self.l1_translation_vec = np.array([0, 0, self.L1], dtype=float)
        self.l2_translation_vec = np.array([self.L2, 0, 0], dtype=float)
        self.l3_translation_vec = np.array([0, 0, self.L3], dtype=float)
        self.tilt_translation_vec = np.array([0, 0, self.wrist_arm_length], dtype=float)

    def calc_tilt_angle(self, r, h, perpendicular=True):
        lens_2_target_z_angle = math.degrees(math.atan(h / r))
        tilt_angle = 90 - (lens_2_target_z_angle if not perpendicular else 0) 
        return tilt_angle

    def calc_target_position(self, r, theta, h):
        target_angle = self.lens.angle + theta  # angle with respect to the camera center-line
        target_angle_rad = math.radians(target_angle)
        dx = r * math.cos(target_angle_rad)
        dy = r * math.sin(target_angle_rad)
        target_position = self.lens.position + np.array([dx, dy, h])

        return target_position

    def calc_yaw_and_base_angles(self, target_pos):
        # calc all vectors and positions
        lens_2_target_vec = (target_pos - self.lens.position)[:-1]
        lens_2_target_norm = np.linalg.norm(lens_2_target_vec)

        if lens_2_target_norm < 1:
            raise ValueError("Target is to close to the lens.")

        lens_2_target_perpenducular_dir_vec = np.array([-lens_2_target_vec[1], lens_2_target_vec[0]]) / lens_2_target_norm
        yaw_axis_2_arget_dist = np.linalg.norm(self.l1_translation_vec[:-1] + self.l2_translation_vec[:-1]) # circle radius is l1 and l2 projections to xy (after they have been tilted and l1 also been rolled)
        yaw_axis_2_target_vec = yaw_axis_2_arget_dist * lens_2_target_perpenducular_dir_vec

        yaw_axis_position = target_pos[:-1] - yaw_axis_2_target_vec

        # calc A, B, C constants from the vectors and positions
        v_x, v_y = yaw_axis_2_target_vec
        w_x, w_y = yaw_axis_position - self.base_position[:-1]
        A = v_x * w_x + v_y * w_y
        B = -v_y * w_x + v_x * w_y
        C = -self.L2 ** 2

        # solvig for delta and phi, where:
        # delta = +-(beta - phi)
        R = math.hypot(A, B)
        if abs(C) > R:
            raise ValueError("Target unreachable: yaw axis too close to target")
        phi = math.atan2(B, A)
        delta = math.acos(C / R)

        # getting beta and thetha
        solutions = []
        for sign in (1.0, -1.0):
            beta = phi + sign * delta
            v_r = np.array([v_x * math.cos(beta) - v_y * math.sin(beta), v_x * math.sin(beta) + v_y * math.cos(beta),])
            q = yaw_axis_position + v_r
            base_angle = math.atan2(q[1] - self.base_position[1], q[0] - self.base_position[0])
            solutions.append((math.degrees(beta), math.degrees(base_angle)))

        # sortig by closenes to world heading 0, on the signed (-180, 180] representation
        def signed(angle_deg):
            return ((angle_deg + 180.0) % 360.0) - 180.0
        
        solutions.sort(key=lambda solution: abs(signed(solution[0])) + abs(signed(solution[1])))

        return solutions[0], q

    def calc_wrist_position(self, target_position, yaw_position_xy):
        yaw_position_z = (target_position + self.l1_translation_vec + self.l2_translation_vec + self.l3_translation_vec)[-1]
        yaw_position = np.array([yaw_position_xy[0], yaw_position_xy[1], yaw_position_z])

        wrist_position = yaw_position + self.tilt_translation_vec
        return wrist_position

    def calc_shoulder_and_elbow_angles(self, wrist_position):
        shoulder_2_wrist_vec = wrist_position - self.shoulder_servo_position
        xy_projection_dist = math.sqrt(shoulder_2_wrist_vec[0]**2 + shoulder_2_wrist_vec[1]**2)
        shoulder_2_wrist_vec_angle = math.degrees(math.atan(shoulder_2_wrist_vec[-1] / xy_projection_dist))
        shoulder_2_wrist_length = np.linalg.norm(shoulder_2_wrist_vec)

        # cosine rule
        a = self.shoulder_arm_length
        b = self.elbow_arm_length
        c = shoulder_2_wrist_length

        if a + b < c: raise ValueError(f"Target unreachable")

        shoulder_angle = math.degrees(
            math.acos(max(-1.0, min(1.0, (a**2 + c**2 - b**2) / (2 * a * c))))
        )
        elbow_angle = math.degrees(
            math.acos(max(-1.0, min(1.0, (a**2 + b**2 - c**2) / (2 * a * b))))
        )

        shoulder_angle += shoulder_2_wrist_vec_angle  # adding the vector angle to make the shoulder_angle is with respect to the zero angle

        return shoulder_angle, elbow_angle
        
    def calc_angle_config(self, r, theta, h, roll_angle=0, wrist_perpendicular_2_ground=True):
        self.reset_translation_vectors()  # each call starts from a clean, unrotated baseline
        self.l1_translation_vec = rotate_vector(self.l1_translation_vec, roll_angle, 'y')

        target_pos = self.calc_target_position(r, theta, h)
        tilt_angle = self.calc_tilt_angle(r, h, wrist_perpendicular_2_ground)

        delta_2_tilt = 90 - tilt_angle
        self.l1_translation_vec = rotate_vector(self.l1_translation_vec, delta_2_tilt, 'x')
        self.l2_translation_vec = rotate_vector(self.l2_translation_vec, delta_2_tilt, 'x')
        self.l3_translation_vec = rotate_vector(self.l3_translation_vec, delta_2_tilt, 'x')
        self.tilt_translation_vec = rotate_vector(self.tilt_translation_vec, delta_2_tilt, 'x')

        angles, yaw_pos_xy = self.calc_yaw_and_base_angles(target_pos)
        yaw_angle, base_angle = angles

        self.l1_translation_vec = rotate_vector(self.l1_translation_vec, yaw_angle, 'z')
        self.l2_translation_vec = rotate_vector(self.l2_translation_vec, yaw_angle, 'z')
        self.tilt_translation_vec = rotate_vector(self.tilt_translation_vec, -base_angle, 'z') # -base_angle cause we want to rotate the vector opposite to the base angle

        wrist_pos = self.calc_wrist_position(target_pos, yaw_pos_xy)
        shoulder_angle, elbow_angle = self.calc_shoulder_and_elbow_angles(wrist_pos)
        wrist_angle = 90 - (180 - shoulder_angle - elbow_angle)

        angle_config = [base_angle, shoulder_angle, elbow_angle, wrist_angle, yaw_angle, roll_angle]
        return angle_config

    def to_servo_angels(self, angle_config):
        base_angle, shoulder_angle, elbow_angle, wrist_angle, yaw_angle, roll_angle = angle_config
        
        servo_base_angle = round((self.base_logical_zero - 90) + base_angle)
        servo_shoulder_angle = round(self.shoulder_logical_zero + shoulder_angle)
        servo_elbow_angle = round(self.elbow_logical_zero + (180 - elbow_angle))
        servo_wrist_angle = round(self.wrist_logical_zero - wrist_angle)
        servo_yaw_angle = round(yaw_angle + self.yaw_logical_zero)
        servo_roll_angle = round(self.roll_logical_zero + roll_angle)

        servo_angles = [servo_base_angle, servo_shoulder_angle, servo_elbow_angle, servo_wrist_angle, servo_yaw_angle, servo_roll_angle]

        for (name, (min_angle, max_angle)), angle in zip(self.servo_operating_ranges, servo_angles):
            if not (min_angle <= angle <= max_angle):
                raise ValueError(f"{name}: angle {angle} outside operating range {(min_angle, max_angle)}")

        return servo_angles

    def compile(self, program_path):

        with open(program_path, "r") as f:
            lines = f.readlines()

        angle_configs = []
        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue

            tokens = line.split()
            if len(tokens) % 2 != 0:
                raise ValueError(f"Malformed calibration program line {line_num}: {raw_line!r}")

            point = dict(zip(tokens[0::2], tokens[1::2]))
            missing_keys = {"r", "a", "h"} - point.keys()
            if missing_keys:
                raise ValueError(f"Calibration program line {line_num} missing {sorted(missing_keys)}: {raw_line!r}")

            r, theta, h = float(point["r"]), float(point["a"]), float(point["h"])
            roll_angle = float(point["ro"]) if "ro" in point else 0

            try:
                angle_config = self.calc_angle_config(r, theta, h, roll_angle=roll_angle)
                angle_configs.append(self.to_servo_angels(angle_config))
            except ValueError as e:
                raise ValueError(f"Calibration program line {line_num}: {e}") from e

        return angle_configs
