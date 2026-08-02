from arm_connection import ArmConnection


ac = ArmConnection("192.168.1.216", 65432)
ac.connect_arm()
ac.send({"test": None})

