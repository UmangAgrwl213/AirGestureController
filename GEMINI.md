# AirGestureController

AirGestureController is a computer vision project designed to control computer functions using hand gestures. It leverages MediaPipe for hand tracking and OpenCV for video processing.

## Project Overview

The project aims to provide a touchless interface by translating hand movements and gestures captured by a webcam into system commands (like mouse movement, clicks, or keyboard shortcuts) using PyAutoGUI.

### Main Technologies
- **Python**: Core programming language.
- **MediaPipe**: For high-fidelity hand and finger tracking.
- **OpenCV**: For real-time computer vision and image processing.
- **PyAutoGUI**: For controlling the mouse and keyboard based on detected gestures.
- **NumPy**: For mathematical operations on landmark coordinates.

### Architecture
- **Entry Points**: 
    - `run.py`: Recommended entry point. Handles environment checks and launches the UI.
    - `ui.py`: The "AirGesture Terminal" dashboard for configuration and control.
    - `main.py`: The core hand tracking and system control loop.
- **Modules**:
    - `modules/hand_tracking.py`: Encapsulates MediaPipe Hand tracking logic.
    - `modules/controller.py`: Logic for mapping detected gestures to system actions (Mouse, Hotkeys, Media).

## Building and Running

### Prerequisites
- **Python**: 3.10 or 3.12 (Recommended). 
  - *Note*: MediaPipe's legacy `solutions` API (used in this project) currently has compatibility issues with Python 3.13 on some systems.
- Webcam

### Setup (Recommended via `uv`)
1. Ensure `uv` is installed (`pip install uv`).
2. Create and prepare the environment:
   ```powershell
   uv venv --python 3.10
   uv pip install -r requirements.txt
   ```

### Execution
Launch the full dashboard:
```powershell
python run.py
```

To bypass the launcher (if in a compatible environment):
```powershell
python ui.py
```

## Standalone Desktop Application

The project can be bundled into a standalone Windows executable that doesn't require a Python installation.

### Building the App
To rebuild the executable:
1. Ensure PyInstaller is installed: `pip install pyinstaller`
2. Run the build command: `pyinstaller AirGestureController.spec`

### Using the App
The built application is located in `dist/AirGestureController/`.
- **AirGestureController.exe**: Launches the main gesture control system.
- **Settings.bat**: Launches the configuration GUI to remap gestures and macros.
- **config.json**: You can edit this file directly or use the Settings GUI.

## Development Conventions

- **Modularity**: New features should be added as modules within the `modules/` directory.
- **Class-Based Design**: Prefer encapsulating complex logic (like detection or control) within classes.
- **Documentation**: Use inline comments to explain logic, especially coordinate transformations and gesture definitions.
- **Citations**: Some parts of the code use `[cite: ...]` comments; maintain this style if following specific tutorials or documentation.

## TODO / Roadmap
- [ ] Implement gesture recognition logic in `modules/controller.py`.
- [ ] Integrate `PyAutoGUI` for mouse control (movement and clicks).
- [ ] Add support for multiple gestures (e.g., scrolling, volume control).
- [ ] Improve detection robustness in varying lighting conditions.
