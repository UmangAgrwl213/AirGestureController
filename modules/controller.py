import pyautogui
import numpy as np
import json
import os
import time

class SystemController:
    def __init__(self, frame_width=640, frame_height=480, smoothing=7):
        # 1. Screen settings
        self.screen_w, self.screen_h = pyautogui.size()
        
        # 2. Frame reduction (Active Area)
        self.frame_reduction = 120
        self.active_w = frame_width - (2 * self.frame_reduction)
        self.active_h = frame_height - (2 * self.frame_reduction)
        
        # 3. Dynamic Smoothing (EMA)
        self.smoothing = smoothing
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
            "open_palm": {"active": False, "frames": 0}
        }
        self.threshold_frames = 2
        
        # 5. Stability & Control
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
                        self.config = json.load(f).get("mappings", {})
                    self.last_config_time = mod_time
                    print("Configuration reloaded.")
        except Exception as e:
            print(f"Error loading config: {e}")
            if not hasattr(self, 'config'): self.config = {}

    def execute_action(self, mapping):
        action = mapping.get("action")
        if action == "click":
            pyautogui.click(button=mapping.get("button", "left"))
        elif action == "hotkey":
            pyautogui.hotkey(*mapping.get("keys", []))
        elif action == "press":
            pyautogui.press(mapping.get("key"))

    def move_mouse(self, raw_x, raw_y):
        if self.clutch_mode:
            return

        # 1. Map to screen
        x_mapped = np.interp(raw_x, (self.frame_reduction, self.frame_reduction + self.active_w), (0, self.screen_w))
        y_mapped = np.interp(raw_y, (self.frame_reduction, self.frame_reduction + self.active_h), (0, self.screen_h))
        
        # 2. Velocity-Adaptive Smoothing
        # Faster movement = less smoothing (raw input)
        # Slower movement = more smoothing (precision)
        dist_raw = np.hypot(x_mapped - self.prev_x, y_mapped - self.prev_y)
        dynamic_smoothing = max(1, self.smoothing - (dist_raw / 10))
        
        self.curr_x = self.prev_x + (x_mapped - self.prev_x) / dynamic_smoothing
        self.curr_y = self.prev_y + (y_mapped - self.prev_y) / dynamic_smoothing
        
        # 3. Precision Deadzone
        if np.hypot(self.curr_x - self.prev_x, self.curr_y - self.prev_y) > self.deadzone:
            # Mirrored screen
            pyautogui.moveTo(self.screen_w - self.curr_x, self.curr_y)
            self.prev_x, self.prev_y = self.curr_x, self.curr_y

    def process_gestures(self, lm_list, fingers):
        if not lm_list: return None

        # 1. Hand scale for adaptive thresholds
        x0, y0 = lm_list[0][3], lm_list[0][4]
        x9, y9 = lm_list[9][3], lm_list[9][4]
        hand_scale = np.hypot(x9 - x0, y9 - y0)
        pinch_threshold = hand_scale * 0.15

        # 2. Detect Raw States
        raw_states = {
            "pinch_index": np.hypot(lm_list[8][3] - lm_list[4][3], lm_list[8][4] - lm_list[4][4]) < pinch_threshold,
            "pinch_middle": np.hypot(lm_list[12][3] - lm_list[4][3], lm_list[12][4] - lm_list[4][4]) < pinch_threshold,
            "pinch_ring": np.hypot(lm_list[16][3] - lm_list[4][3], lm_list[16][4] - lm_list[4][4]) < pinch_threshold,
            "pinch_pinky": np.hypot(lm_list[20][3] - lm_list[4][3], lm_list[20][4] - lm_list[4][4]) < pinch_threshold,
            "fist": sum(fingers) == 0,
            "victory": fingers == [0, 1, 1, 0, 0],
            "open_palm": fingers == [1, 1, 1, 1, 1]
        }

        # 3. Clutch Mechanism
        # If thumb is tucked in but other fingers are up, stop movement
        if fingers == [0, 1, 1, 1, 1]:
            self.clutch_mode = True
        else:
            self.clutch_mode = False

        # 4. Trigger and Debounce
        triggered = None
        for gesture, is_active in raw_states.items():
            if is_active:
                self.states[gesture]["frames"] += 1
                if self.states[gesture]["frames"] >= self.threshold_frames:
                    if not self.states[gesture]["active"]:
                        if gesture in self.config:
                            self.execute_action(self.config[gesture])
                            triggered = gesture
                        self.states[gesture]["active"] = True
            else:
                self.states[gesture]["frames"] = 0
                self.states[gesture]["active"] = False
        
        return triggered
