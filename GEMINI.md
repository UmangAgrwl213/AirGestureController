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
    - `main.py`: Currently serves as a distance testing script for pinch gestures.
    - `gesture_engine.py`: A basic hand tracking visualization script.
- **Modules**:
    - `modules/hand_tracking.py`: Contains the `HandDetector` class, which encapsulates the MediaPipe Hands solution.
    - `modules/controller.py`: (Planned) Logic for mapping detected gestures to system actions.

## Building and Running

### Prerequisites
- **Python**: 3.10 or 3.12 (Recommended). 
  - *Note*: MediaPipe's legacy `solutions` API (used in this project) currently has compatibility issues with Python 3.13 on some systems.
- Webcam

### Setup
1. Clone the repository.
2. Install the required dependencies (ensure you are using a compatible Python version):
   ```bash
   pip install mediapipe==0.10.9 opencv-python pyautogui numpy
   ```

### Execution
To run the hand tracking test:
```bash
python gesture_engine.py
```

To run the gesture distance test:
```bash
python main.py
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
