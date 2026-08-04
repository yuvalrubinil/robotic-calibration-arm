import os
import random
import tempfile
from kinematics_compiler import KinematicsCompiler

def test_random_values():
    print("--- Testing calculate_ik with random values ---")
    compiler = KinematicsCompiler()
    
    # We will temporarily set some dummy lengths if they are 0
    # so we don't just get flat 0 output due to the domain error check.
    if compiler.lengths.get("shoulder_arm", 0) == 0:
        print("Note: Lengths in JSON are currently 0. Temporarily mocking lengths for the math test.")
        compiler.lengths["shoulder_arm"] = 10.0
        compiler.lengths["elbow_arm"] = 10.0
        compiler.lengths["wrist_arm"] = 5.0
        
    for i in range(1, 6):
        # Generate random reachable coordinates
        radius = random.uniform(5.0, 15.0)
        theta = random.uniform(-180.0, 180.0)
        height = random.uniform(0.0, 10.0)
        
        result = compiler.calculate_ik(radius, theta, height)
        print(f"Test {i}:")
        print(f"  Input : (radius={radius:.2f}, theta={theta:.2f}, height={height:.2f})")
        print(f"  Output: {{0: {result[0]:.2f}, 1: {result[1]:.2f}, 2: {result[2]:.2f}, 3: {result[3]:.2f}}}\n")

def test_file_compilation():
    print("--- Testing compile_from_file ---")
    compiler = KinematicsCompiler()
    
    if compiler.lengths.get("shoulder_arm", 0) == 0:
        compiler.lengths["shoulder_arm"] = 10.0
        compiler.lengths["elbow_arm"] = 10.0
        compiler.lengths["wrist_arm"] = 5.0

    # Create dummy input file with targets
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as infile:
        infile.write("(12.5, 45, 5.0)\n")
        infile.write("(8.0, -30, 2.0)\n")
        infile.write("(invalid_line_to_test_error_handling)\n")
        infile.write("(15.0, 90, 8.0)\n")
        in_name = infile.name

    out_name = in_name.replace('.txt', '_out.txt')

    print(f"Running compile_from_file()...")
    compiler.compile_from_file(in_name, out_name)

    print("\nInput File Contents:")
    with open(in_name, 'r') as f:
        print(f.read().strip())

    print("\nOutput File Contents:")
    with open(out_name, 'r') as f:
        print(f.read().strip())
        
    # Cleanup temp files
    os.remove(in_name)
    os.remove(out_name)

if __name__ == "__main__":
    test_random_values()
    print("")
    test_file_compilation()
