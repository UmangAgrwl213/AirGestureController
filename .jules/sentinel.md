## 2024-05-24 - Unauthenticated Network Access via 0.0.0.0 Binding
**Vulnerability:** The FastAPI web interface (`server.py` and `launcher.py`) was binding to `0.0.0.0` (all interfaces) by default, exposing the local gesture control web server to the entire local network without any authentication.
**Learning:** This could allow a malicious actor on the same network to arbitrarily execute hotkeys, mouse clicks, and cursor movements on the user's desktop, effectively resulting in remote command execution via PyAutoGUI.
**Prevention:** Web control interfaces for desktop applications that have system-level access should bind strictly to `127.0.0.1` (localhost) to ensure only the local user can interact with them.
