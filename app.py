import sys
import tkinter as tk
import main
import ui

def start_ui():
    root = tk.Tk()
    app = ui.GestureConfigApp(root)
    root.mainloop()

def start_main():
    # Check for camera ID argument
    cam_index = 1
    if len(sys.argv) > 1:
        try:
            cam_index = int(sys.argv[1])
        except ValueError:
            pass
    main.main(cam_index)

if __name__ == "__main__":
    if "--ui" in sys.argv:
        start_ui()
    else:
        start_main()
