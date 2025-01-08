import os
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
from diff_viewer import DiffViewer
from settings_dialog import SettingsDialog
from data_merge import DataMerger, MergeConfig
from fchat_logs import ChatLogs
from localization import L10N

class ChatLogMerger(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        
        self.title(L10N.get_text("app_title"))
        self.geometry("800x600")
        
        # Config path
        self.config_path = os.path.expanduser("~/.fchat_merger/config.json")
        
        # Initialize merger
        self.merger = DataMerger()
        
        # Load or show settings dialog
        if not self._load_config():
            self._show_settings_dialog()
        
        self._create_ui()
        self._load_accounts()
        
    def _create_ui(self):
        """Create the main UI"""
        # Main container with padding
        main_container = ttk.Frame(self, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for account selection and settings
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Account selection
        account_frame = ttk.LabelFrame(top_frame, text=L10N.get_text("account_label"), padding=5)
        account_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.account_combo = ttk.Combobox(account_frame, state="readonly")
        self.account_combo.pack(fill=tk.X, padx=5)
        self.account_combo.bind("<<ComboboxSelected>>", lambda e: self._load_conversations())
        
        # Settings button
        ttk.Button(
            top_frame,
            text=L10N.get_text("settings_button"),
            command=self._show_settings_dialog,
            style="info.Outline.TButton"
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Database list
        db_frame = ttk.LabelFrame(main_container, text=L10N.get_text("available_databases"), padding=10)
        db_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        self.tree = ttk.Treeview(
            db_frame,
            columns=("conversation", "device_a", "device_b"),
            show="headings"
        )
        
        self.tree.column("conversation", width=200)
        self.tree.column("device_a", width=30)
        self.tree.column("device_b", width=30)
        
        self.tree.tag_configure('different', foreground='red')
        self.tree.tag_configure('common', foreground='gray')
        
        self.tree.heading("conversation", text=L10N.get_text("conversation_column"))
        self.tree.heading("device_a", text=L10N.get_text("data_a_column"))
        self.tree.heading("device_b", text=L10N.get_text("data_b_column"))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(db_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind context menu
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        # Merge options
        options_frame = ttk.LabelFrame(main_container, text=L10N.get_text("merge_options"), padding=10)
        options_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Target device selection
        self.target_var = tk.StringVar(value="both")
        
        ttk.Radiobutton(
            options_frame,
            text=L10N.get_text("both_devices"),
            value="both",
            variable=self.target_var
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            options_frame,
            text=L10N.get_text("device_a_only"),
            value="device_a",
            variable=self.target_var
        ).pack(side=tk.LEFT)
        
        ttk.Radiobutton(
            options_frame,
            text=L10N.get_text("device_b_only"),
            value="device_b",
            variable=self.target_var
        ).pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text=L10N.get_text("view_selected"),
            command=self._view_conversation,
            style="info.TButton"
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            btn_frame,
            text=L10N.get_text("merge_selected"),
            command=lambda: self._merge_selected(),
            style="success.TButton"
        ).pack(side=tk.RIGHT)
        
    def _load_config(self):
        """Load config from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.device_a_path = config["device_a_path"]
                    self.device_b_path = config["device_b_path"]
                    return True
            except:
                pass
        return False
        
    def _show_settings_dialog(self):
        """Show settings dialog"""
        def on_save(config):
            self.device_a_path = config["device_a_path"]
            self.device_b_path = config["device_b_path"]
            self._load_accounts()
            
        dialog = SettingsDialog(self, self.config_path, on_save)
        dialog.wait_window()
        
    def _load_accounts(self):
        """Load accounts from databases"""
        try:
            self.device_a_db = ChatLogs(self.device_a_path)
            self.device_b_db = ChatLogs(self.device_b_path)
            
            # Get unique accounts from both devices
            accounts = sorted(set(self.device_a_db.get_available_characters()) | set(self.device_b_db.get_available_characters()))
            
            # Update combobox
            self.account_combo["values"] = accounts
            if accounts:
                self.account_combo.set(accounts[0])
                self._load_conversations()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load databases: {str(e)}")
            
    def _load_conversations(self):
        """Load conversations for selected account"""
        self.tree.delete(*self.tree.get_children())
        account = self.account_combo.get()
        
        if not account:
            return
            
        # Get conversations from both devices
        convos_a = set(self.device_a_db.get_conversations(account))
        convos_b = set(self.device_b_db.get_conversations(account))
        
        # Add all conversations to tree
        for convo in sorted(convos_a | convos_b):
            in_a = convo in convos_a
            in_b = convo in convos_b
            conversation_key = convo[0]
            size_a = self.device_a_db.get_backlog_size(account, conversation_key)
            if size_a > 0:
                lastlog_a = self.device_a_db.get_backlog(account, conversation_key, 1)[0]
            else:
                lastlog_a = None
            size_b = self.device_b_db.get_backlog_size(account, conversation_key)
            if size_b > 0:
                lastlog_b = self.device_b_db.get_backlog(account, conversation_key, 1)[0]
            else:
                lastlog_b = None
            
            if size_a != size_b:
                different = False
                if lastlog_a is None:
                    if lastlog_b:
                        different = True 
                    device_a = f"{size_a}"
                else:
                    if lastlog_b and lastlog_a.time != lastlog_b.time:
                        different = True 
                    device_a = f"{size_a} ({lastlog_a.time})"
                if lastlog_b is None:
                    if lastlog_a:
                        different = True 
                    device_b = f"{size_b}"
                else:
                    if lastlog_a and lastlog_a.time != lastlog_b.time:
                        different = True 
                    device_b = f"{size_b} ({lastlog_b.time})"
            
            self.tree.insert(
                "",
                "end",
                text=f"{convo[1]} ({convo[0]})",
                values=(
                    f"{convo[1]} ({convo[0]})",
                    size_a,
                    size_b,
                    convo[0],
                    convo[1]
                ),
                tags=('different',) if different else ('common',)
            )
            
    def _show_context_menu(self, event):
        """Show context menu for tree item"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=L10N.get_text("view_conversation"), command=self._view_conversation)
        
        # Create merge sub-menu
        merge_menu = tk.Menu(menu, tearoff=0)
        merge_menu.add_command(
            label=L10N.get_text("merge_to_a"),
            command=lambda: self._merge_selected("device_a")
        )
        merge_menu.add_command(
            label=L10N.get_text("merge_to_b"),
            command=lambda: self._merge_selected("device_b")
        )
        merge_menu.add_separator()
        merge_menu.add_command(
            label=L10N.get_text("merge_to_both"),
            command=lambda: self._merge_selected("both")
        )
        
        menu.add_cascade(label=L10N.get_text("merge_menu"), menu=merge_menu)
        menu.post(event.x_root, event.y_root)
        
    def _view_conversation(self):
        """Open diff viewer for selected conversation"""
        selected = self.tree.selection()
        if not selected:
            return
            
        account = self.account_combo.get()
        conversation = self.tree.item(selected[0])["values"][3]
        
        diff_viewer = DiffViewer(
            self,
            account,
            conversation,
            self.device_a_db,
            self.device_b_db
        )
        
    def _merge_selected(self, target=None):
        """Merge selected conversations"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                L10N.get_text("no_selection"),
                L10N.get_text("select_conversation")
            )
            return
            
        account = self.account_combo.get()
        # Use provided target or fallback to radio button selection
        target = target or self.target_var.get()
        
        for item in selected:
            conversation = [  self.tree.item(item)["values"][3],  self.tree.item(item)["values"][4]]
            
            # Create merge config
            config = MergeConfig(
                account=account,
                conversation=conversation,
                device_a_path=self.device_a_path,
                device_b_path=self.device_b_path,
                target=target
            )
            
            # Perform merge
            try:
                self.merger.merge_conversation(config)
            except Exception as e:
                messagebox.showerror(
                    L10N.get_text("merge_error"),
                    L10N.get_text("merge_error_msg", conversation=conversation, error=str(e))
                )
                return
        
        messagebox.showinfo(
            L10N.get_text("merge_success"),
            L10N.get_text("merge_success_msg", count=len(selected))
        )
        
        # Refresh the view
        self._load_conversations()

if __name__ == "__main__":
    app = ChatLogMerger()
    app.mainloop()
