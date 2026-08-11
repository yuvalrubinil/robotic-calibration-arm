from ik_compiler import IKCompiler

ikc = IKCompiler(r"/home/yuval-rubin/Projects/robotic_calibration_arm/src/arm/config.json")
angle_config = ikc.calc_angle_config(r=10, theta=0, h=4, roll_angle=0.0, wrist_perpendicular_2_ground=False)
print(angle_config)
