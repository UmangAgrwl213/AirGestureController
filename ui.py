import customtkinter as ctk
import json
import os
import sys
import cv2
import time
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from tkinter import messagebox
from modules.engine import GestureEngine

# --- HIGH-FIDELITY DESIGN TOKENS (The "A" Tier) ---
COLORS = {
    "background": "#08090A",       # Absolute Matte Obsidian
    "sidebar": "#040506",          # Deepest Black
    "surface": "#121417",          # Slightly elevated surface
    "surface_glass": "#1A1D21",    # Glassmorphism base
    "accent_primary": "#A8C3B0",   # Premium Desaturated Sage
    "accent_secondary": "#D4A373", # Brushed Copper
    "accent_glow": "#4C6B5F",      # Deep accent glow
    "text_h1": "#FFFFFF",
    "text_body": "#9BA3AF",
    "border_subtle": "#21262D",
    "status_active": "#52B788",
    "status_error": "#E63946"
}

# Layout constants for the "Rhythm"
P_SM = 8
P_MD = 16
P_LG = 32
RADIUS = 12

class GlassCard(ctk.CTkFrame):
    """Custom high-fidelity card with simulated glassmorphism and subtle lighting."""
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, fg_color=COLORS["surface"], 
                         border_color=COLORS["border_subtle"], border_width=1, 
                         corner_radius=RADIUS, **kwargs)
        if title:
            header_frame = ctk.CTkFrame(self, fg_color="transparent")
            header_frame.pack(fill="x", padx=P_MD, pady=(P_MD, 0))
            
            # Subtle accent indicator
            ctk.CTkLabel(header_frame, text="┃", text_color=COLORS["accent_primary"], 
                          font=("Consolas", 18, "bold")).pack(side="left")
            
            self.title_label = ctk.CTkLabel(header_frame, text=title.upper(), 
                                            font=("Rajdhani", 14, "bold") if sys.platform != "win32" else ("Consolas", 12, "bold"),
                                            text_color=COLORS["text_h1"])
            self.title_label.pack(side="left", padx=P_SM)

class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew", padx=P_LG, pady=P_LG)
        self.container.grid_columnconfigure(0, weight=3)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=3)
        self.container.grid_rowconfigure(1, weight=1)

        # 1. Main View (Sensor Analytics)
        self.monitor_card = GlassCard(self.container, title="Sensor Stream Matrix")
        self.monitor_card.grid(row=0, column=0, sticky="nsew", padx=(0, P_MD), pady=(0, P_MD))
        
        self.cam_label = ctk.CTkLabel(self.monitor_card, text="AWAITING SYSTEM INITIALIZATION...", 
                                       font=("Consolas", 14), text_color=COLORS["text_body"])
        self.cam_label.pack(expand=True, fill="both", padx=P_MD, pady=P_MD)

        # 2. Control Module
        self.ctrl_card = GlassCard(self.container, title="Neural Engine Link")
        self.ctrl_card.grid(row=0, column=1, sticky="nsew", pady=(0, P_MD))

        # Status readout
        self.status_frame = ctk.CTkFrame(self.ctrl_card, fg_color="#0A0B0D", corner_radius=6)
        self.status_frame.pack(fill="x", padx=P_MD, pady=P_MD)
        
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color=COLORS["status_error"], font=("Consolas", 20))
        self.status_dot.pack(side="left", padx=(12, 8), pady=12)
        
        self.status_text = ctk.CTkLabel(self.status_frame, text="LINK_OFFLINE", 
                                         font=("Consolas", 12, "bold"), text_color=COLORS["text_h1"])
        self.status_text.pack(side="left", pady=12)

        self.launch_btn = ctk.CTkButton(self.ctrl_card, text="CONNECT BIO-LINK", 
                                        command=self.controller.toggle_engine, 
                                        height=60, corner_radius=RADIUS, 
                                        fg_color=COLORS["accent_primary"],
                                        text_color=COLORS["sidebar"],
                                        hover_color=COLORS["accent_glow"],
                                        font=("Consolas", 14, "bold"))
        self.launch_btn.pack(fill="x", padx=P_MD, pady=P_MD)

        # 3. Log Module (The Bottom "Drawer")
        self.log_card = GlassCard(self.container, title="Real-Time Analytics")
        self.log_card.grid(row=1, column=0, columnspan=2, sticky="nsew")
        
        self.log_text = ctk.CTkTextbox(self.log_card, font=("Consolas", 11), 
                                        fg_color="transparent", text_color=COLORS["accent_primary"])
        self.log_text.pack(fill="both", expand=True, padx=P_MD, pady=P_SM)
        self.log_text.insert("end", ">> SYSTEM::READY_FOR_BIO_LINK\n")
        self.log_text.configure(state="disabled")

    def log(self, message):
        def type_text(msg, idx=0):
            if idx < len(msg):
                self.log_text.configure(state="normal")
                self.log_text.insert("end", msg[idx])
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
                self.after(5, lambda: type_text(msg, idx + 1))
        type_text(f">> {message}\n")

class GesturesPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        base_gestures = [
            "pinch_index", "pinch_middle", "pinch_ring", "pinch_pinky", 
            "fist", "victory", "open_palm", "swipe_left", "swipe_right", 
            "swipe_up", "swipe_down", "poke_forward", "pull_back"
        ]
        self.gestures = []
        for g in base_gestures:
            self.gestures.append(f"{g}_right")
            self.gestures.append(f"{g}_left")
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=P_LG, pady=P_LG)
        ctk.CTkLabel(header, text="MAPPING_ARCHITECTURE", font=("Consolas", 28, "bold"), text_color=COLORS["text_h1"]).pack(side="left")
        
        self.matrix_card = GlassCard(self, title="Macro Definitions")
        self.matrix_card.grid(row=1, column=0, sticky="nsew", padx=P_LG, pady=(0, P_LG))

        self.scroll_frame = ctk.CTkScrollableFrame(self.matrix_card, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=P_SM, pady=P_SM)
        self.scroll_frame.grid_columnconfigure(2, weight=1)

        self.ui_elements = {}
        for i, gesture in enumerate(self.gestures):
            name = gesture.replace("_", " ").upper()
            row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row.grid(row=i, column=0, columnspan=6, sticky="ew", pady=2)
            row.grid_columnconfigure(2, weight=1)

            ctk.CTkLabel(row, text=f"{i:02d}", font=("Consolas", 10), text_color=COLORS["text_muted"]).grid(row=0, column=0, padx=10)
            ctk.CTkLabel(row, text=name, font=("Consolas", 11, "bold"), width=180, anchor="w", text_color=COLORS["text_h1"]).grid(row=0, column=1, padx=5)

            config = self.controller.mappings.get(gesture, {"action": "click", "button": "left"})
            action_var = ctk.StringVar(value=config.get("action", "click"))
            cb = ctk.CTkComboBox(row, values=["click", "hotkey", "press", "scroll", "drag"], variable=action_var, 
                                 width=100, font=("Consolas", 11), fg_color=COLORS["sidebar"], border_color=COLORS["border_subtle"],
                                 command=lambda _: self.controller.save_mappings())
            cb.grid(row=0, column=2, padx=2, sticky="w")

            val_var = ctk.StringVar(value=self.get_config_val(config))
            ent = ctk.CTkEntry(row, textvariable=val_var, width=140, font=("Consolas", 11),
                               fg_color=COLORS["sidebar"], border_color=COLORS["border_subtle"])
            ent.grid(row=0, column=3, padx=5)
            val_var.trace_add("write", lambda *args, g=gesture: self.controller.update_mapping_val(g, val_var.get()))

            rec_btn = ctk.CTkButton(row, text="CAPTURE", width=60, height=28, font=("Consolas", 10, "bold"), 
                                     fg_color="transparent", border_width=1, border_color=COLORS["accent_secondary"],
                                     text_color=COLORS["accent_secondary"], hover_color="#2A1A1A",
                                     command=lambda g=gesture: self.start_recording(g))
            rec_btn.grid(row=0, column=4, padx=5)

            self.ui_elements[gesture] = {"action": action_var, "value": val_var, "rec_btn": rec_btn}

    def get_config_val(self, config):
        a = config.get("action")
        if a == "click": return config.get("button", "left")
        if a == "hotkey": return ",".join(config.get("keys", []))
        return config.get("key", "")

    def start_recording(self, gesture):
        if hasattr(self, 'recording_for') and self.recording_for:
            self.ui_elements[self.recording_for]["rec_btn"].configure(text="CAPTURE", fg_color="transparent")
        self.recording_for = gesture
        self.ui_elements[gesture]["rec_btn"].configure(text="LISTENING", fg_color="#301A10")
        self.focus_set()

    def handle_keypress(self, key_name):
        if hasattr(self, 'recording_for') and self.recording_for:
            self.ui_elements[self.recording_for]["value"].set(key_name)
            self.ui_elements[self.recording_for]["action"].set("press")
            self.ui_elements[self.recording_for]["rec_btn"].configure(text="CAPTURE", fg_color="transparent")
            self.recording_for = None
            self.controller.save_mappings()

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="ENGINE_CALIBRATION", font=("Consolas", 28, "bold"), text_color=COLORS["text_h1"]).pack(pady=P_LG, padx=P_LG, anchor="w")

        # 1€ Filter Calibration
        card = GlassCard(self, title="Precision Physics")
        card.pack(fill="x", padx=P_LG, pady=P_SM)
        ctk.CTkLabel(card, text="MOTION_SMOOTHING_THRESHOLD", font=("Consolas", 11)).pack(padx=P_MD, pady=(P_MD, 0), anchor="w")
        self.smooth_slider = ctk.CTkSlider(card, from_=1, to=20, number_of_steps=19, 
                                          button_color=COLORS["accent_primary"],
                                          button_hover_color=COLORS["accent_secondary"],
                                          command=self.controller.update_smoothing)
        self.smooth_slider.set(self.controller.current_settings.get("smoothing", 7))
        self.smooth_slider.pack(fill="x", padx=P_MD, pady=(P_SM, P_MD))

        # Hardware Sensor Selection
        card2 = GlassCard(self, title="Hardware interface")
        card2.pack(fill="x", padx=P_LG, pady=P_SM)
        ctk.CTkLabel(card2, text="ACTIVE_IMAGING_SENSOR_ID", font=("Consolas", 11)).pack(padx=P_MD, pady=(P_MD, 0), anchor="w")
        self.cam_var = ctk.StringVar(value=str(self.controller.current_settings.get("camera_id", 1)))
        ctk.CTkComboBox(card2, values=["0", "1", "2"], variable=self.cam_var, 
                         fg_color=COLORS["sidebar"], border_color=COLORS["border_subtle"],
                         command=self.controller.update_camera).pack(padx=P_MD, pady=(P_SM, P_MD), anchor="w")

        # Confidence Calibration
        card3 = GlassCard(self, title="Neural Sensitivity")
        card3.pack(fill="x", padx=P_LG, pady=P_SM)
        
        ctk.CTkLabel(card3, text="DETECTION_CONFIDENCE", font=("Consolas", 11)).pack(padx=P_MD, pady=(P_MD, 0), anchor="w")
        self.det_slider = ctk.CTkSlider(card3, from_=0.1, to=1.0, number_of_steps=90,
                                        button_color=COLORS["accent_primary"],
                                        command=self.controller.update_detection_con)
        self.det_slider.set(self.controller.current_settings.get("detection_confidence", 0.8))
        self.det_slider.pack(fill="x", padx=P_MD, pady=(P_SM, P_SM))

        ctk.CTkLabel(card3, text="TRACKING_CONFIDENCE", font=("Consolas", 11)).pack(padx=P_MD, pady=(P_MD, 0), anchor="w")
        self.track_slider = ctk.CTkSlider(card3, from_=0.1, to=1.0, number_of_steps=90,
                                          button_color=COLORS["accent_primary"],
                                          command=self.controller.update_tracking_con)
        self.track_slider.set(self.controller.current_settings.get("tracking_confidence", 0.8))
        self.track_slider.pack(fill="x", padx=P_MD, pady=(P_SM, P_MD))

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AirGesture Professional Edition")
        self.geometry("1280x880")
        self.configure(fg_color=COLORS["background"])
        
        self.config_path = "config.json"
        self.engine = None
        self.load_settings()
        self.setup_sidebar()
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_container.pack(side="right", fill="both", expand=True)

        self.pages = {}
        for PageClass in (DashboardPage, GesturesPage, SettingsPage):
            page_name = PageClass.__name__
            page = PageClass(self.main_container, self)
            self.pages[page_name] = page
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page("DashboardPage")
        self.bind("<Key>", self.on_key_press)
        self.update_frame()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="AIR_GESTURE", 
                      font=("Consolas", 22, "bold"), 
                      text_color=COLORS["accent_primary"]).pack(pady=(P_LG, 4))
        ctk.CTkLabel(self.sidebar, text="PROFESSIONAL SUITE", 
                      font=("Consolas", 10, "bold"), 
                      text_color=COLORS["accent_secondary"]).pack(pady=(0, 48))
        
        self.nav_btns = {}
        for label, page in [("COMMAND", "DashboardPage"), ("MATRIX", "GesturesPage"), ("PHYSICS", "SettingsPage")]:
            btn = ctk.CTkButton(self.sidebar, text=f"• {label}", corner_radius=0, height=56, 
                                 fg_color="transparent", text_color=COLORS["text_body"],
                                 font=("Consolas", 14, "bold"), anchor="w",
                                 hover_color=COLORS["surface"],
                                 command=lambda p=page: self.show_page(p))
            btn.pack(fill="x", padx=12, pady=1)
            self.nav_btns[page] = btn

    def show_page(self, page_name):
        for page in self.pages.values(): page.place_forget()
        self.pages[page_name].place(relx=0, rely=0, relwidth=1, relheight=1)
        for name, btn in self.nav_btns.items():
            is_active = (name == page_name)
            btn.configure(text_color=COLORS["accent_primary"] if is_active else COLORS["text_body"],
                          fg_color=COLORS["surface"] if is_active else "transparent")

    def load_settings(self):
        self.current_settings = {"smoothing": 7, "camera_id": 1, "detection_confidence": 0.8, "tracking_confidence": 0.8}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.current_settings.update(data.get("settings", {}))
                    self.mappings = data.get("mappings", {})
            except: self.mappings = {}
        else: self.mappings = {}

    def update_frame(self):
        if self.engine and self.engine.running:
            frame = self.engine.get_frame()
            if frame is not None:
                lbl = self.pages["DashboardPage"].cam_label
                w, h = lbl.winfo_width(), lbl.winfo_height()
                if w > 10:
                    frame = cv2.resize(frame, (w, h))
                    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img_rgb)
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
                    lbl.configure(image=ctk_img, text="")
        self.after(15, self.update_frame)

    def toggle_engine(self):
        dash = self.pages["DashboardPage"]
        if self.engine is None or not self.engine.running:
            try:
                self.engine = GestureEngine(camera_id=int(self.current_settings["camera_id"]), 
                                            smoothing=self.current_settings["smoothing"], 
                                            callback=dash.log)
                self.engine.start()
                dash.status_dot.configure(text_color=COLORS["status_active"])
                dash.status_text.configure(text="LINK_ACTIVE")
                dash.launch_btn.configure(text="TERMINATE BIO-LINK", fg_color="#2A1A1A", 
                                          text_color=COLORS["accent_secondary"], border_color=COLORS["accent_secondary"])
            except Exception as e: messagebox.showerror("BIO_LINK_ERROR", str(e))
        else:
            self.engine.stop()
            dash.status_dot.configure(text_color=COLORS["status_error"])
            dash.status_text.configure(text="LINK_OFFLINE")
            dash.launch_btn.configure(text="CONNECT BIO-LINK", fg_color=COLORS["accent_primary"], 
                                      text_color=COLORS["sidebar"], border_color=COLORS["accent_primary"])
            dash.cam_label.configure(image="", text="SENSOR_FEED_TERMINATED")

    def on_key_press(self, event):
        key = event.keysym.lower()
        mapping = {"return": "enter", "space": "space", "control_l": "ctrl", "alt_l": "alt", "shift_l": "shift", "win_l": "win"}
        self.pages["GesturesPage"].handle_keypress(mapping.get(key, key))

    def update_smoothing(self, val):
        self.current_settings["smoothing"] = int(val)
        if self.engine: self.engine.smoothing = int(val)
        self.save_to_file()

    def update_camera(self, val):
        self.current_settings["camera_id"] = int(val)
        self.save_to_file()

    def update_detection_con(self, val):
        self.current_settings["detection_confidence"] = float(val)
        self.save_to_file()

    def update_tracking_con(self, val):
        self.current_settings["tracking_confidence"] = float(val)
        self.save_to_file()

    def update_mapping_val(self, gesture, val):
        if gesture not in self.mappings: self.mappings[gesture] = {"action": "press"}
        act = self.pages["GesturesPage"].ui_elements[gesture]["action"].get()
        self.mappings[gesture]["action"] = act
        if act == "click": self.mappings[gesture]["button"] = val
        elif act == "hotkey": self.mappings[gesture]["keys"] = [k.strip() for k in val.split(",")]
        else: self.mappings[gesture]["key"] = val
        self.save_to_file()

    def save_mappings(self):
        self.save_to_file()

    def save_to_file(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump({"settings": self.current_settings, "mappings": self.mappings}, f, indent=2)
        except: pass

    def on_closing(self):
        if self.engine: self.engine.stop()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    MainWindow().mainloop()
