import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class GestureConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Air Gesture Settings")
        self.root.geometry("500x400")
        
        self.config_path = "config.json"
        self.mappings = self.load_config()
        
        self.setup_ui()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return json.load(f).get("mappings", {})
        return {}

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Configure Gesture Actions", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 20))

        self.gestures = ["pinch_index", "pinch_middle", "fist"]
        self.ui_elements = {}

        for i, gesture in enumerate(self.gestures):
            ttk.Label(main_frame, text=gesture.replace("_", " ").title() + ":").grid(row=i+1, column=0, sticky=tk.W, pady=10)
            
            # Action Type
            action_var = tk.StringVar(value=self.mappings.get(gesture, {}).get("action", "click"))
            action_cb = ttk.Combobox(main_frame, textvariable=action_var, values=["click", "hotkey", "press"], width=10, state="readonly")
            action_cb.grid(row=i+1, column=1, padx=10)
            
            # Value/Keys
            current_val = ""
            if action_var.get() == "click":
                current_val = self.mappings.get(gesture, {}).get("button", "left")
            elif action_var.get() == "hotkey":
                current_val = ",".join(self.mappings.get(gesture, {}).get("keys", []))
            elif action_var.get() == "press":
                current_val = self.mappings.get(gesture, {}).get("key", "")
            
            value_var = tk.StringVar(value=current_val)
            value_entry = ttk.Entry(main_frame, textvariable=value_var, width=20)
            value_entry.grid(row=i+1, column=2)
            
            self.ui_elements[gesture] = {"action": action_var, "value": value_var}

        # Save Button
        save_btn = ttk.Button(main_frame, text="Save & Apply Settings", command=self.save_config)
        save_btn.grid(row=len(self.gestures)+1, column=0, columnspan=3, pady=30)

        # Instructions
        instr = "Tips:\n- click: left, right, middle\n- hotkey: ctrl,c or win,d\n- press: space, enter, etc."
        ttk.Label(main_frame, text=instr, foreground="gray").grid(row=len(self.gestures)+2, column=0, columnspan=3, sticky=tk.W)

    def save_config(self):
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

        try:
            with open(self.config_path, "w") as f:
                json.dump({"mappings": new_mappings}, f, indent=2)
            messagebox.showinfo("Success", "Settings saved successfully! The controller will apply them instantly.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GestureConfigApp(root)
    root.mainloop()
