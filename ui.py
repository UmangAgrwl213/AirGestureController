import customtkinter as ctk
import json
import os
import subprocess
import sys
from tkinter import messagebox

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- Standard Build Presets ---
PRESETS = {
    "Mouse: Left Click": {"action": "click", "button": "left"},
    "Mouse: Right Click": {"action": "click", "button": "right"},
    "Mouse: Middle Click": {"action": "click", "button": "middle"},
    "System: Show Desktop": {"action": "hotkey", "keys": ["win", "d"]},
    "System: Switch Window": {"action": "hotkey", "keys": ["alt", "tab"]},
    "Media: Play/Pause": {"action": "press", "key": "playpause"},
    "Media: Next Track": {"action": "press", "key": "nexttrack"},
    "Media: Prev Track": {"action": "press", "key": "prevtrack"},
    "Media: Volume Up": {"action": "press", "key": "volumeup"},
    "Media: Volume Down": {"action": "press", "key": "volumedown"},
    "Clipboard: Copy": {"action": "hotkey", "keys": ["ctrl", "c"]},
    "Clipboard: Paste": {"action": "hotkey", "keys": ["ctrl", "v"]},
}

class MacroPopup(ctk.CTkToplevel):
    def __init__(self, parent, mappings, save_callback):
        super().__init__(parent)
        self.title("Gesture Macro Settings")
        self.geometry("750x650")
        self.parent = parent
        self.mappings = mappings
        self.save_callback = save_callback
        self.recording_for = None
        
        self.gestures = [
            "pinch_index", "pinch_middle", "pinch_ring", "pinch_pinky", 
            "fist", "victory", "open_palm"
        ]
        
        self.setup_ui()
        self.attributes("-topmost", True)
        self.bind("<Key>", self.on_key_press)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text="Configure Gesture Macros", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, pady=20, padx=20)

        # Scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Gesture Assignment Table")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(1, weight=0) # Action
        self.scroll_frame.grid_columnconfigure(2, weight=1) # Value
        self.scroll_frame.grid_columnconfigure(3, weight=0) # Record
        self.scroll_frame.grid_columnconfigure(4, weight=0) # Presets

        self.ui_elements = {}

        for i, gesture in enumerate(self.gestures):
            name = gesture.replace("_", " ").title()
            
            # Gesture Name
            ctk.CTkLabel(self.scroll_frame, text=name, font=ctk.CTkFont(size=13, weight="bold"), width=100).grid(row=i, column=0, padx=10, pady=15, sticky="w")

            # Action Selection
            current_config = self.mappings.get(gesture, {"action": "click", "button": "left"})
            action_var = ctk.StringVar(value=current_config.get("action", "click"))
            action_cb = ctk.CTkComboBox(self.scroll_frame, values=["click", "hotkey", "press"], 
                                         variable=action_var, width=90)
            action_cb.grid(row=i, column=1, padx=5, pady=15)

            # Value Entry
            val = ""
            if action_var.get() == "click": val = current_config.get("button", "left")
            elif action_var.get() == "hotkey": val = ",".join(current_config.get("keys", []))
            elif action_var.get() == "press": val = current_config.get("key", "")

            value_var = ctk.StringVar(value=val)
            entry = ctk.CTkEntry(self.scroll_frame, textvariable=value_var, width=150, placeholder_text="key/button")
            entry.grid(row=i, column=2, padx=5, pady=15, sticky="ew")

            # Record Button
            rec_btn = ctk.CTkButton(self.scroll_frame, text="⏺", width=40, height=28, 
                                     fg_color="#34495E", hover_color="#E67E22",
                                     command=lambda g=gesture: self.start_recording(g))
            rec_btn.grid(row=i, column=3, padx=5)

            # Presets Dropdown
            preset_var = ctk.StringVar(value="Select Preset...")
            preset_cb = ctk.CTkComboBox(self.scroll_frame, values=list(PRESETS.keys()), 
                                         variable=preset_var, width=160, 
                                         command=lambda val, g=gesture: self.apply_preset(g, val))
            preset_cb.grid(row=i, column=4, padx=5)

            self.ui_elements[gesture] = {
                "action": action_var, 
                "value": value_var, 
                "rec_btn": rec_btn,
                "preset_cb": preset_cb
            }

        # Footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, pady=20)
        
        self.save_btn = ctk.CTkButton(footer, text="Save & Apply", command=self.save, width=200, height=45, font=ctk.CTkFont(size=15, weight="bold"))
        self.save_btn.pack(side="left", padx=10)

        self.cancel_btn = ctk.CTkButton(footer, text="Cancel", command=self.destroy, fg_color="transparent", border_width=1, width=100)
        self.cancel_btn.pack(side="left", padx=10)

    def apply_preset(self, gesture, preset_name):
        if preset_name in PRESETS:
            config = PRESETS[preset_name]
            self.ui_elements[gesture]["action"].set(config["action"])
            
            if config["action"] == "click":
                self.ui_elements[gesture]["value"].set(config["button"])
            elif config["action"] == "hotkey":
                self.ui_elements[gesture]["value"].set(",".join(config["keys"]))
            elif config["action"] == "press":
                self.ui_elements[gesture]["value"].set(config["key"])
            
            # Reset preset selection text
            self.ui_elements[gesture]["preset_cb"].set("Select Preset...")

    def start_recording(self, gesture):
        # Stop previous recording if any
        if self.recording_for:
            self.ui_elements[self.recording_for]["rec_btn"].configure(text="⏺", fg_color="#34495E")
        
        self.recording_for = gesture
        self.ui_elements[gesture]["rec_btn"].configure(text="Listening...", fg_color="#E67E22")
        self.focus_set() # Ensure window has focus to catch key events

    def on_key_press(self, event):
        if self.recording_for:
            gesture = self.recording_for
            key_name = event.keysym.lower()
            
            # Simple mapping for special keys
            mapping = {"return": "enter", "space": "space", "control_l": "ctrl", "control_r": "ctrl", "alt_l": "alt", "alt_r": "alt", "shift_l": "shift", "shift_r": "shift", "win_l": "win"}
            key_name = mapping.get(key_name, key_name)
            
            self.ui_elements[gesture]["value"].set(key_name)
            self.ui_elements[gesture]["action"].set("press") # Default to press for recorded keys
            
            # Reset button
            self.ui_elements[gesture]["rec_btn"].configure(text="⏺", fg_color="#34495E")
            self.recording_for = None

    def save(self):
        new_mappings = {}
        for gesture, elements in self.ui_elements.items():
            action = elements["action"].get()
            value = elements["value"].get().strip()
            
            if not value: continue
            
            mapping = {"action": action}
            if action == "click":
                mapping["button"] = value
            elif action == "hotkey":
                mapping["keys"] = [k.strip() for k in value.split(",")]
            elif action == "press":
                mapping["key"] = value
                
            new_mappings[gesture] = mapping
        
        self.save_callback(new_mappings)
        self.destroy()

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AirGesture Controller")
        self.geometry("450x480")
        
        self.config_path = "config.json"
        self.process = None
        
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        self.title_label = ctk.CTkLabel(self, text="AirGesture", font=ctk.CTkFont(size=36, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=(40, 5))
        
        self.subtitle_label = ctk.CTkLabel(self, text="ADVANCED TOUCHLESS CONTROL", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3B8ED0")
        self.subtitle_label.grid(row=1, column=0, pady=(0, 40))

        # Status Card
        self.status_card = ctk.CTkFrame(self, fg_color=("gray85", "gray15"), height=90)
        self.status_card.grid(row=2, column=0, padx=40, sticky="ew", pady=10)
        self.status_card.grid_propagate(False)
        self.status_card.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(self.status_card, text="●", text_color="#E74C3C", font=ctk.CTkFont(size=28))
        self.status_dot.grid(row=0, column=0, padx=(25, 10), pady=30)
        
        self.status_text = ctk.CTkLabel(self.status_card, text="SYSTEM OFFLINE", font=ctk.CTkFont(size=16, weight="bold"))
        self.status_text.grid(row=0, column=1, sticky="w", pady=30)

        # Action Buttons
        self.launch_btn = ctk.CTkButton(self, text="Launch Engine", command=self.toggle_engine, 
                                        height=55, corner_radius=12, font=ctk.CTkFont(size=18, weight="bold"))
        self.launch_btn.grid(row=3, column=0, pady=(40, 15), padx=40, sticky="ew")

        self.settings_btn = ctk.CTkButton(self, text="Configure Macros & Presets", command=self.open_settings,
                                          height=45, fg_color="transparent", border_width=2, corner_radius=12)
        self.settings_btn.grid(row=4, column=0, pady=5, padx=60, sticky="ew")

    def toggle_engine(self):
        if self.process is None:
            try:
                self.process = subprocess.Popen([sys.executable, "main.py", "1"])
                self.status_dot.configure(text_color="#2ECC71")
                self.status_text.configure(text="SYSTEM ACTIVE")
                self.launch_btn.configure(text="Stop Engine", fg_color="#E74C3C", hover_color="#C0392B")
            except Exception as e:
                messagebox.showerror("Error", f"Launch failed: {e}")
        else:
            self.process.terminate()
            self.process = None
            self.status_dot.configure(text_color="#E74C3C")
            self.status_text.configure(text="SYSTEM OFFLINE")
            self.launch_btn.configure(text="Launch Engine", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#3276AD", "#144870"])

    def open_settings(self):
        mappings = {}
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                mappings = json.load(f).get("mappings", {})
        
        MacroPopup(self, mappings, self.save_config)

    def save_config(self, new_mappings):
        try:
            with open(self.config_path, "w") as f:
                json.dump({"mappings": new_mappings}, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
