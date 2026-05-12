# AirGesture: Design System & Architecture Spec

## 1. Aesthetic Vision: "Industrial Minimal"
The application moves away from generic consumer GUI patterns toward a high-density, tool-first aesthetic inspired by professional telemetry and terminal interfaces.

### Core Principles
- **Functional Density**: Information is prioritized over white space. Every pixel should serve a functional purpose.
- **Monospaced Hierarchy**: Use of **Consolas** or **Roboto Mono** to create a technical, "under-the-hood" atmosphere.
- **High Contrast Dark Mode**: Deep black backgrounds (#0A0A0A) with vivid primary accents (Electric Blue #3B8ED0) and status-driven colors (Success: #2ECC71, Warning: #F1C40F, Critical: #E74C3C).
- **Brutalist Borders**: Thin, sharp 1px borders (#333333) instead of soft shadows to define boundaries.

## 2. Technical Architecture

### A. The Kinematic Engine (`modules/engine.py`)
- **Physics**: Implementation of the **One Euro Filter** (1€ Filter). 
  - *Low Speed*: High smoothing to eliminate hand tremor jitter.
  - *High Speed*: Low smoothing to eliminate cursor lag during flick movements.
- **Multi-Threading**: The engine operates in a dedicated thread, emitting frames to the UI at 30-60 FPS without blocking interaction.
- **Temporal Analysis**: Gesture triggers use a "Frame-Window" debounce (2-frame minimum) to ensure intentionality.

### B. The Mapping Matrix (`ui.py`)
- **Master-Detail Layout**: A list of all supported gestures (Pinch, Fist, Victory, Palm, etc.) with immediate access to:
  - Action Type (Click, Hotkey, Press)
  - Parameter Value (Key name or Button index)
  - Macro Recorder (Listening mode)
  - Build Presets (Quick-apply standard actions)
- **Hot-Reloading**: Changes in the Matrix are written to `config.json` and immediately detected by the Engine's polling loop.

### C. The Compatibility Launcher (`run.py`)
- **Environment Management**: Detects Python 3.13 incompatibility.
- **Venv Hijacking**: If a local `.venv` exists, it re-executes the application using the venv's python executable, abstracting the environment setup for the user.
- **Arg Passing**: Forwards camera indices and flags to the internal engine.

### D. The Integrated Terminal
- **Purpose**: Real-time observability.
- **Style**: Green-on-Black scrolling textbox.
- **Log Levels**: 
  - `>>` (System Event)
  - `[!]` (Error/Warning)
  - `TRGR:` (Gesture Activation)

## 3. Gesture Library

| ID | Name | Detection Logic | Suggested Use |
|----|------|-----------------|---------------|
| 00 | PINCH_INDEX | Index-Thumb distance < threshold | Left Click |
| 01 | PINCH_MIDDLE | Middle-Thumb distance < threshold | Right Click |
| 02 | FIST | Sum(Fingers) == 0 | Show Desktop |
| 03 | SWIPE_UP/DOWN | Vertical velocity > threshold | Volume / Scrolling |
| 04 | VICTORY | [0, 1, 1, 0, 0] finger state | App Switcher |

## 4. Design Guidelines for Future UI Overhaul
- **Icons**: Use **Lucide-React** or **Heroicons** SVG paths.
- **Buttons**: Square corners (0-4px radius) for a rugged feel.
- **Feed Overlay**: Add a scan-line effect or minimal crosshair over the live camera feed.
