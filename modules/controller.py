import pyautogui
import numpy as np
import json
import os
import time

class OneEuroFilter:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0, freq=30):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.freq = freq
        self.x_prev = None
        self.dx_prev = 0

    def smoothing_factor(self, cutoff):
        r = 2 * np.pi * cutoff / self.freq
        return r / (r + 1)

    def exponential_smoothing(self, x, x_prev, alpha):
        return alpha * x + (1 - alpha) * x_prev

    def __call__(self, x):
        t_e = 1.0 / self.freq
        if self.x_prev is None:
            self.x_prev = x
            return x
        
        dx = (x - self.x_prev) / t_e
        edx = self.exponential_smoothing(dx, self.dx_prev, self.smoothing_factor(self.d_cutoff))
        self.dx_prev = edx
        
        cutoff = self.min_cutoff + self.beta * abs(edx)
        alpha = self.smoothing_factor(cutoff)
        result = self.exponential_smoothing(x, self.x_prev, alpha)
        self.x_prev = result
        return result

class SystemController:
    def __init__(self, frame_width=640, frame_height=480, smoothing=7):
        # 1. Screen settings
        self.screen_w, self.screen_h = pyautogui.size()
        
        # 2. Frame reduction (Active Area)
        self.frame_reduction = 120
        self.active_w = frame_width - (2 * self.frame_reduction)
        self.active_h = frame_height - (2 * self.frame_reduction)
        
        # 3. Precision Smoothing (1 Euro Filter)
        # min_cutoff: Low speed jitter (Lower = more stable)
        # beta: High speed lag (Higher = less lag)
        self.filter_x = OneEuroFilter(min_cutoff=0.5, beta=0.01)
        self.filter_y = OneEuroFilter(min_cutoff=0.5, beta=0.01)
        
        self.prev_x, self.prev_y = 0, 0
        self.curr_x, self.curr_y = 0, 0
        
        # 4. Gesture States
        self.states = {
            "pinch_index": {"active": False, "frames": 0},
            "pinch_middle": {"active": False, "frames": 0},
            "pinch_ring": {"active": False, "frames": 0},
            "pinch_pinky": {"active": False, "frames": 0},
            "fist": {"active": False, "frames": 0},
            "victory": {"active": False, "frames": 0},
            "open_palm": {"active": False, "frames": 0},
            "swipe_left": {"active": False, "frames": 0},
            "swipe_right": {"active": False, "frames": 0},
            "swipe_up": {"active": False, "frames": 0},
            "swipe_down": {"active": False, "frames": 0},
            "poke_forward": {"active": False, "frames": 0},
            "pull_back": {"active": False, "frames": 0},
            "double_pinch_index": {"active": False, "frames": 0},
            "drag_index": {"active": False, "frames": 0}
        }
        self.threshold_frames = 2
        
        # 5. Motion History for Swipes & Depth
        self.history = []
        self.history_len = 10
        self.swipe_threshold = 0.15 
        self.swipe_cooldown = 0.5   
        self.last_swipe_time = 0
        
        # 6. Depth Analysis (Z-axis)
        self.depth_history = []
        self.depth_len = 5
        self.poke_threshold = 0.05 # Z-change threshold
        
        # 7. Temporal Tracking
        self.last_pinch_time = 0
        self.double_pinch_window = 0.4 # Seconds
        self.is_dragging = False
        self.drag_origin = (0, 0)
        self.drag_threshold = 30 # Pixels movement to start drag
        
        # 8. Stability & Control
        self.deadzone = 3 
        self.clutch_mode = False # If true, cursor movement stops
        
        # 6. Load Config
        self.config_path = "config.json"
        self.last_config_time = 0
        self.load_config()
        
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                mod_time = os.path.getmtime(self.config_path)
                if mod_time > self.last_config_time:
                    with open(self.config_path, "r") as f:
                        data = json.load(f)
                        self.config = data.get("mappings", {})
                        settings = data.get("settings", {})
                        self.smoothing = settings.get("smoothing", 7)
                        self.detection_con = settings.get("detection_confidence", 0.8)
                        self.track_con = settings.get("tracking_confidence", 0.8)
                    self.last_config_time = mod_time
                    print("Configuration reloaded.")
        except Exception as e:
            print(f"Error loading config: {e}")
            if not hasattr(self, 'config'): self.config = {}

    def execute_action(self, mapping):
        if not mapping: return
        try:
            action = mapping.get("action")
            if action == "click":
                pyautogui.click(button=mapping.get("button", "left"), clicks=mapping.get("clicks", 1))
            elif action == "hotkey":
                pyautogui.hotkey(*mapping.get("keys", []))
            elif action == "press":
                pyautogui.press(mapping.get("key"))
            elif action == "scroll":
                pyautogui.scroll(mapping.get("amount", 100))
            elif action == "drag":
                # Toggle drag
                if not self.is_dragging:
                    pyautogui.mouseDown(button=mapping.get("button", "left"))
                    self.is_dragging = True
                else:
                    pyautogui.mouseUp(button=mapping.get("button", "left"))
                    self.is_dragging = False
        except Exception as e:
            print(f"Action Execution Failed: {e}")

    def move_mouse(self, raw_x, raw_y):
        if self.clutch_mode:
            return

        try:
            # 1. Map to screen
            x_mapped = np.interp(raw_x, (self.frame_reduction, self.frame_reduction + self.active_w), (0, self.screen_w))
            y_mapped = np.interp(raw_y, (self.frame_reduction, self.frame_reduction + self.active_h), (0, self.screen_h))
            
            # 2. 1 Euro Filter Smoothing
            self.curr_x = self.filter_x(x_mapped)
            self.curr_y = self.filter_y(y_mapped)
            
            # 3. Validation
            if not np.isfinite(self.curr_x) or not np.isfinite(self.curr_y):
                return

            # 4. Execution with fail-safe
            if np.hypot(self.curr_x - self.prev_x, self.curr_y - self.prev_y) > self.deadzone:
                if self.is_dragging:
                    pyautogui.dragTo(self.curr_x, self.curr_y, _pause=False)
                else:
                    pyautogui.moveTo(self.curr_x, self.curr_y, _pause=False)
                self.prev_x, self.prev_y = self.curr_x, self.curr_y
        except Exception as e:
            # Silently handle common OS-level movement errors to prevent loop death
            pass

    def process_gestures(self, lm_list, fingers, handedness="Right", current_shape=None):
        if not lm_list: 
            self.history = []
            self.depth_history = []
            if self.is_dragging:
                pyautogui.mouseUp()
                self.is_dragging = False
            return None

        # 1. Update Motion & Depth History
        curr_pos = (lm_list[9][3], lm_list[9][4])
        curr_z = lm_list[9][5] # Index 5 is normalized Z
        
        self.history.append(curr_pos)
        self.depth_history.append(curr_z)
        if len(self.history) > self.history_len: self.history.pop(0)
        if len(self.depth_history) > self.depth_len: self.depth_history.pop(0)

        # 2. Hand scale for adaptive thresholds
        x0, y0 = lm_list[0][3], lm_list[0][4]
        x9, y9 = lm_list[9][3], lm_list[9][4]
        hand_scale = np.hypot(x9 - x0, y9 - y0)
        pinch_threshold = hand_scale * 0.15

        # 3. Depth-Based Gestures (Poke/Pull)
        depth_triggered = None
        if len(self.depth_history) == self.depth_len:
            dz = self.depth_history[-1] - self.depth_history[0]
            if dz < -self.poke_threshold: depth_triggered = f"poke_forward_{handedness.lower()}"
            elif dz > self.poke_threshold: depth_triggered = f"pull_back_{handedness.lower()}"
            
            if depth_triggered and depth_triggered in self.config:
                self.execute_action(self.config[depth_triggered])
                self.depth_history = []
                return depth_triggered

        # 4. Swipe Detection
        swipe_triggered = None
        if len(self.history) == self.history_len and (time.time() - self.last_swipe_time) > self.swipe_cooldown:
            dx = self.history[-1][0] - self.history[0][0]
            dy = self.history[-1][1] - self.history[0][1]
            
            if abs(dx) > self.swipe_threshold or abs(dy) > self.swipe_threshold:
                direction = ""
                if abs(dx) > abs(dy):
                    if dx > self.swipe_threshold: direction = "left" # Mirrored
                    elif dx < -self.swipe_threshold: direction = "right"
                else:
                    if dy > self.swipe_threshold: direction = "down"
                    elif dy < -self.swipe_threshold: direction = "up"
                
                if direction:
                    specific_name = f"swipe_{direction}_{handedness.lower()}"
                    general_name = f"swipe_{direction}"
                    target_name = specific_name if specific_name in self.config else general_name if general_name in self.config else None
                    
                    if target_name:
                        self.execute_action(self.config[target_name])
                        self.last_swipe_time = time.time()
                        self.history = []
                        return target_name

        # 5. Pinch Logic
        is_pinching = np.hypot(lm_list[8][3] - lm_list[4][3], lm_list[8][4] - lm_list[4][4]) < pinch_threshold
        
        # 6. Double Pinch Logic
        if is_pinching and not self.states["pinch_index"]["active"]:
            curr_time = time.time()
            if (curr_time - self.last_pinch_time) < self.double_pinch_window:
                name = f"double_pinch_index_{handedness.lower()}"
                if name in self.config: self.execute_action(self.config[name])
                self.last_pinch_time = 0
                return name
            self.last_pinch_time = curr_time

        # 7. Clutch Mechanism
        self.clutch_mode = (current_shape == "clutch")

        # 8. Continuous Actions (Scroll/Volume)
        # Scroll allowed for both hands
        if current_shape == "victory" and len(self.history) >= 2:
            dy = self.history[-1][1] - self.history[-2][1]
            if abs(dy) > 2: # Sensitivity threshold
                scroll_amount = int(-dy * 20) # Scale as needed
                pyautogui.scroll(scroll_amount)
        
        # Volume allowed for both hands
        if current_shape == "three_fingers" and len(self.history) >= 2:
            dy = self.history[-1][1] - self.history[-2][1]
            if abs(dy) > 5:
                if dy < 0: pyautogui.press('volumeup')
                else: pyautogui.press('volumedown')

        # 9. Trigger and Debounce (Shape-aware)
        triggered = None
        if current_shape:
            specific_name = f"{current_shape}_{handedness.lower()}"
            general_name = current_shape
            
            if not self.states.get(current_shape, {}).get("active", False):
                target_name = specific_name if specific_name in self.config else general_name if general_name in self.config else None
                if target_name:
                    mapping = self.config[target_name]
                    # All actions (Click/Drag/Scroll/Hotkey) allowed for both hands now
                    self.execute_action(mapping)
                    triggered = target_name
                
                if current_shape in self.states: self.states[current_shape]["active"] = True
        else:
            # Reset all shape states when no shape is detected
            for s in self.states:
                if "pinch" not in s and "swipe" not in s and "poke" not in s:
                    self.states[s]["active"] = False

        # Keep existing pinch state for double-pinch tracking
        self.states["pinch_index"]["active"] = is_pinching
        
        return triggered
