import subprocess
import sys
import os
import time
import webbrowser

def check_mediapipe():
    try:
        import mediapipe as mp
        _ = mp.solutions.hands
        return True
    except (ImportError, AttributeError):
        return False

def main():
    print("--- AirGesture Web Unified Launcher ---")
    
    # 1. Environment Check
    if not check_mediapipe():
        print("\nERROR: Incompatible Python environment detected.")
        print("MediaPipe legacy 'solutions' are not supported here (likely 3.13+).")
        
        print("\nAttempting to locate compatible Python 3.10/3.12...")
        for ver in ["3.12", "3.10"]:
            try:
                # Check if this specific version is available and compatible
                result = subprocess.run(["py", f"-{ver}", "-c", "import mediapipe as mp; _ = mp.solutions.hands"], 
                                         capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"Found compatible Python {ver}. Relaunching server...")
                    # We launch server.py directly with the correct python
                    subprocess.run(["py", f"-{ver}", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"])
                    return
            except FileNotFoundError:
                continue
        
        print("\nCould not find a compatible environment automatically.")
        print("Please use Python 3.10 or 3.12.")
        input("\nPress Enter to exit...")
        return

    # 2. Start FastAPI Server
    print("Initializing Web Server (FastAPI)...")
    # ... rest of logic
    # We use uvicorn to run our server.py
    # Using 'sys.executable' ensures we use the same environment
    cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"]
    
    server_process = subprocess.Popen(cmd)
    
    # 3. Wait for server to warm up
    time.sleep(2)
    
    # 4. Open Browser
    url = "http://localhost:8000"
    print(f"\nSUCCESS: Server running at {url}")
    print("Opening your default browser...")
    webbrowser.open(url)
    
    print("\n[!] Keep this terminal open to maintain the Bio-Link.")
    print("[!] Press Ctrl+C here or use 'TERMINATE' in the web UI to stop.")
    
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down Bio-Link...")
        server_process.terminate()

if __name__ == "__main__":
    main()
