import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
import json
import os
from localization import L10N

class SettingsDialog(ttk.Toplevel):
    def __init__(self, parent, config_path, on_save=None):
        super().__init__(parent)
        self.title(L10N.get_text("settings_title"))
        self.geometry("600x300")
        
        self.config_path = config_path
        self.on_save = on_save
        
        # Default F-Chat data path
        self.default_path = os.path.join(os.environ["APPDATA"], "fchat", "data")
        
        # Load existing config if it exists
        self.config = self._load_config()
        
        self._create_ui()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
    def _create_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Data folders frame with grid layout
        data_folders_frame = ttk.LabelFrame(main_frame, text=L10N.get_text("data_folders"), padding=10)
        data_folders_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Configure grid columns
        data_folders_frame.columnconfigure(1, weight=1)  # Make entry column expandable
        
        # Device A row
        ttk.Label(data_folders_frame, text=L10N.get_text("device_a")).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="e")
        self.device_a_path = ttk.StringVar(value=self.config.get("device_a_path", ""))
        ttk.Entry(data_folders_frame, textvariable=self.device_a_path, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(data_folders_frame, text=L10N.get_text("browse_button"), command=lambda: self._browse_path("device_a_path")).grid(row=0, column=2, padx=5, pady=5)
        
        # Device B row
        ttk.Label(data_folders_frame, text=L10N.get_text("device_b")).grid(row=1, column=0, padx=(0, 10), pady=5, sticky="e")
        self.device_b_path = ttk.StringVar(value=self.config.get("device_b_path", ""))
        ttk.Entry(data_folders_frame, textvariable=self.device_b_path, width=50).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(data_folders_frame, text=L10N.get_text("browse_button"), command=lambda: self._browse_path("device_b_path")).grid(row=1, column=2, padx=5, pady=5)
        
        # Help text
        help_label = ttk.Label(
            data_folders_frame,
            text=L10N.get_text("settings_help"),
            justify=tk.LEFT,
            wraplength=500,
            style="info.TLabel"
        )
        help_label.grid(row=2, column=0, columnspan=3, padx=5, pady=(10, 5), sticky="w")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(button_frame, text=L10N.get_text("save_button"), command=self._save_settings, style="success.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text=L10N.get_text("cancel_button"), command=self.destroy, style="danger.Outline.TButton").pack(side=tk.RIGHT)
        
    def _browse_path(self, target):
        """Open file dialog to select database path"""
        current_path = getattr(self, target).get()
        initial_dir = current_path if current_path else self.default_path
        
        path = filedialog.askdirectory(
            title=f"Select {target.replace('_', ' ').title()} Path",
            initialdir=initial_dir
        )
        if path:
            getattr(self, target).set(path)
            
    def _load_config(self):
        """Load config from file if it exists"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
        
    def _save_settings(self):
        """Save settings to config file"""
        config = {
            "device_a_path": self.device_a_path.get(),
            "device_b_path": self.device_b_path.get()
        }
        
        # Validate paths
        if not all(config.values()):
            tk.messagebox.showerror("Error", L10N.get_text("select_paths"))
            return
            
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save config
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        # Call save callback if provided
        if self.on_save:
            self.on_save(config)
            
        self.destroy()
