# Repository Guidelines

## Project Structure & Module Organization
This repository is a Python desktop-computer-vision project for hand-gesture control.

- `main.py`: primary runtime loop (camera capture, landmark processing, UI window).
- `run.py`: compatibility launcher that selects a Python version supporting MediaPipe.
- `gesture_engine.py`: gesture interpretation logic entry point.
- `modules/`: reusable components:
  - `hand_tracking.py` for landmark detection.
  - `controller.py` for gesture-to-action behavior.
- `assets/`: static project assets (images, docs, or reference files).

Keep new runtime logic in `modules/` and keep top-level scripts thin.

## Build, Test, and Development Commands
- Install dependencies: `pip install -r requirements.txt`
- Run app directly: `python main.py`
- Run with launcher (recommended on Windows): `python run.py`
- Pass camera index: `python run.py 1`

Use `run.py` when working across multiple local Python installations (it checks MediaPipe compatibility).

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation.
- Use `snake_case` for functions/variables, `PascalCase` for classes, lowercase module names.
- Keep functions focused; move reusable logic from scripts into `modules/`.
- Prefer explicit imports and short, descriptive names (`cam_index`, `lm_list`, `detector`).

If you add formatting/lint tooling, prefer `black` and `ruff` and document any new commands here.

## Testing Guidelines
There is currently no committed automated test suite. For new features:

- Add tests under `tests/` using `pytest`.
- Name files `test_<module>.py` and tests `test_<behavior>()`.
- Prioritize unit tests for gesture classification thresholds and controller actions.

Run tests with: `pytest -q`

For camera-dependent behavior, include manual verification steps in PR notes (device, OS, camera index used).

## Commit & Pull Request Guidelines
Git history is currently minimal, so use Conventional Commits going forward:

- `feat: add pinch gesture smoothing`
- `fix: handle camera read failure on startup`
- `docs: update launcher instructions`

PRs should include:
- Clear summary of behavior changes and affected files.
- Linked issue (if available).
- Manual test notes (command run, expected vs. actual behavior).
- Short demo screenshot/GIF for UI or gesture-flow changes.

## Security & Configuration Tips
- Do not commit virtual environments, secrets, or local machine paths.
- Pin critical dependency versions when reproducibility issues appear (especially `mediapipe`).
- Validate platform-specific behavior (Windows camera/device permissions) before release.
