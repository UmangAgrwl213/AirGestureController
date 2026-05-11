import subprocess
import sys
import os

def check_python_version(cmd_list):
    try:
        # Check for mediapipe solutions
        result = subprocess.run(cmd_list + ["-c", "import mediapipe as mp; mp.solutions.hands"], 
                                capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def main():
    print("--- AirGestureController Launcher ---")
    
    # 0. Check for UI flag
    if "--ui" in sys.argv:
        print("Launching Configuration GUI...")
        # Try current python, then 3.10
        if subprocess.run([sys.executable, "ui.py"]).returncode == 0:
            return
        subprocess.run(["py", "-3.10", "ui.py"])
        return

    # 1. Try current python
    current_py = sys.executable
    print(f"Checking current Python ({sys.version.split()[0]})...")
    if check_python_version([current_py]):
        print("Current Python is compatible. Launching main.py...")
        subprocess.run([current_py, "main.py"] + sys.argv[1:])
        return

    # 2. Try py -3.10
    print("Checking Python 3.10 via 'py -3.10'...")
    if check_python_version(["py", "-3.10"]):
        print("Python 3.10 found and compatible. Launching main.py...")
        subprocess.run(["py", "-3.10", "main.py"] + sys.argv[1:])
        return

    # 3. Try py -3.12
    print("Checking Python 3.12 via 'py -3.12'...")
    if check_python_version(["py", "-3.12"]):
        print("Python 3.12 found and compatible. Launching main.py...")
        subprocess.run(["py", "-3.12", "main.py"] + sys.argv[1:])
        return

    print("\nERROR: No compatible Python environment found.")
    print("MediaPipe legacy 'solutions' are not supported in your default Python (likely 3.13+).")
    print("Please install Python 3.10 or 3.12 and run:")
    print("  pip install mediapipe==0.10.9 opencv-python pyautogui numpy")

if __name__ == "__main__":
    main()
