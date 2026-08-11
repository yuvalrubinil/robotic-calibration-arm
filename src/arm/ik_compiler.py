import math
import numpy as np
import json
from lens import Lens


class IKCompiler:
    def __init__(self, arm_config):
        with open(arm_config, "r") as f:
            config = json.load(f)

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

        # camera lenses
        self.left_lens = Lens(lenses['left_lens'])
        self.right_lens = Lens(lenses['right_lens'])
        self.lens = self.right_lens

        # positions
        self.base_position = np.array(servos["0"]["position"], dtype=float)
        self.shoulder_servo_position = np.array(servos["1"]["position"], dtype=float)

        # lofical zeros
        self.base_logical_zero = servos["0"]["logical_zero"]
        self.shoulder_logical_zero = servos["1"]["logical_zero"]
        self.elbow_logical_zero = servos["2"]["logical_zero"]
        self.wrist_logical_zero = servos["3"]["logical_zero"]
        self.yaw_logical_zero = servos["4"]["logical_zero"]
        self.roll_logical_zero = servos["5"]["logical_zero"]


    def calc_target_position(self, r, theta, h):
        target_angle = self.lens.angle + theta  # angle with respect to the camera center-line
        target_angle_rad = math.radians(target_angle)
        dx = r * math.cos(target_angle_rad)
        dy = r * math.sin(target_angle_rad)
        target_position = self.lens.position + np.array([dx, dy, h])

        return target_position

    def calc_wrist_angle(self, r, h, perpendicular_2_ground=True):
        if perpendicular_2_ground:
            return 180
        else:
            pass

    def calc_yaw_and_base_angles(self, target_pos):
        # calc all vectors and positions
        lens_2_target_vec = (target_pos - self.lens.position)[:-1]
        lens_2_target_norm = np.linalg.norm(lens_2_target_vec)

        if lens_2_target_norm < 1:
            raise ValueError("Target is to close to the lens.")

        lens_2_target_perpenducular_vec = np.array([-lens_2_target_vec[1], lens_2_target_vec[0]]) / lens_2_target_norm
        l2_translation_vec = self.L2 * lens_2_target_perpenducular_vec

        yaw_axis_position = target_pos[:-1] - l2_translation_vec

        # calc A, B, C constants from the vectors and positions
        v_x, v_y = l2_translation_vec
        w_x, w_y = yaw_axis_position - self.base_position[:-1]
        A = v_x * w_x + v_y * w_y
        B = -v_y * w_x + v_x * w_y
        C = -self.L2 ** 2

        # solvig for delta and phi, where:
        # delta = +-(beta - phi)
        R = math.hypot(A, B)
        phi = math.atan2(B, A)
        delta = math.acos(max(-1.0, min(1.0, C / R)))

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

    def calc_wrist_position(self, target_pos, wrist_x, wrist_y):
        # right now assuming no tilt
        wrist_z = target_pos[2] + self.L1 + self.L3
        wrist_pos = np.array([wrist_x, wrist_y, wrist_z])
        return wrist_pos

    def calc_shoulder_and_elbow_angles(self, wrist_position):
        shoulder_2_wrist = wrist_position - self.shoulder_servo_position
        shoulder_2_wrist_length = np.linalg.norm(shoulder_2_wrist)

        # cosine rule
        a = self.shoulder_arm_length
        b = self.elbow_arm_length
        c = shoulder_2_wrist_length

        shoulder_angle = math.degrees(
            math.acos(max(-1.0, min(1.0, (a**2 + c**2 - b**2) / (2 * a * c))))
        )
        elbow_angle = math.degrees(
            math.acos(max(-1.0, min(1.0, (a**2 + b**2 - c**2) / (2 * a * b))))
        )
        elbow_angle -= (90 - shoulder_angle) # removing the shoulder share of the angle

        return shoulder_angle, elbow_angle
        

    def calc_angle_config(self, r, theta, h, roll_angle=0.0, wrist_perpendicular_2_ground=True):
        target_pos = self.calc_target_position(r, theta, h)

        wrist_angle = self.calc_wrist_angle(r, h, wrist_perpendicular_2_ground)

        angles, wrist_pos = self.calc_yaw_and_base_angles(target_pos)
        yaw_angle, base_angle = angles
        wrist_x, wrist_y = wrist_pos
        wrist_pos = self.calc_wrist_position(target_pos, wrist_x, wrist_y)
        shoulder_angle, elbow_angle = self.calc_shoulder_and_elbow_angles(wrist_pos)

        angle_config = [base_angle, shoulder_angle, elbow_angle, wrist_angle, yaw_angle, roll_angle]
        servo_angle_config = self.to_servo_angels(angle_config)
        return servo_angle_config


    def to_servo_angels(self, angle_config):
        base_angle, shoulder_angle, elbow_angle, _, yaw_angle, roll_angle = angle_config
        
        servo_base_angle = round(base_angle + (self.base_logical_zero - 90))
        servo_shoulder_angle = round(shoulder_angle + self.shoulder_logical_zero)
        servo_elbow_angle = round(self.elbow_logical_zero + elbow_angle)
        servo_wrist_angle = round(self.wrist_logical_zero - elbow_angle)
        servo_yaw_angle = round(yaw_angle + self.yaw_logical_zero)
        servo_roll_angle = round(roll_angle)

        return [servo_base_angle, servo_shoulder_angle, servo_elbow_angle, servo_wrist_angle, servo_yaw_angle, servo_roll_angle]


    


    