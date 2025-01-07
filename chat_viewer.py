import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from fchat_logs import ChatLogs
from typing import List
from datetime import datetime
from dateutil.tz import tzlocal 
import argparse

LOCAL_TZ = tzlocal()

class ChatViewer(ttk.Window):
    def __init__(self, database_path: str, character: str, conversation: str):
        super().__init__(themename="darkly")
        
        self.title(f"F-Chat Viewer - {character}/{conversation}")
        self.geometry("800x600")
        
        # Initialize database
        self.chat_logs = ChatLogs(database_path)
        self.character = character
        self.conversation = conversation
        
        self._create_ui()
        self._load_dates()
        
    def _create_ui(self):
        """Create the main UI components"""
        # Create main container
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Date selector at top
        date_frame = ttk.Frame(main_container)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(date_frame, text="Select Date:").pack(side=tk.LEFT)
        self.date_combo = ttk.Combobox(date_frame, state="readonly", width=30)
        self.date_combo.pack(side=tk.LEFT, padx=5)
        self.date_combo.bind("<<ComboboxSelected>>", self._on_date_selected)
        
        # Chat display area
        chat_frame = ttk.Frame(main_container)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbar
        self.chat_text = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        
        # Configure tags for different message types
        self.chat_text.tag_configure("timestamp", foreground="#888888")
        self.chat_text.tag_configure("sender", foreground="#4CAF50", font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_configure("message", foreground="#ffffff")
        self.chat_text.tag_configure("system", foreground="#FF9800", font=("Segoe UI", 10, "italic"))
        
        # Pack text widget and scrollbar
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Make text widget read-only
        self.chat_text.configure(state=tk.DISABLED)
        
    def _load_dates(self):
        """Load available dates for the conversation"""
        try:
            dates : List[datetime] = self.chat_logs.get_log_dates(self.character, self.conversation)
            self.date_combo["values"] = [d.strftime("%Y-%m-%d") for d in sorted(dates)]
            if self.date_combo["values"]:
                self.date_combo.set(self.date_combo["values"][-1])
                self._on_date_selected(None)
        except Exception as e:
            print(f"Error loading dates: {e}")
            
    def _on_date_selected(self, event):
        """Handle date selection"""
        try:
            selected_date = datetime.strptime(
                self.date_combo.get(), 
                "%Y-%m-%d"
            ).replace(tzinfo=LOCAL_TZ)
            messages = self.chat_logs.get_backlog(self.character, self.conversation, date=selected_date)
            
            # Clear current display
            self.chat_text.configure(state=tk.NORMAL)
            self.chat_text.delete(1.0, tk.END)
            
            # Display messages
            for msg in messages:
                # Format timestamp
                timestamp = msg.time.strftime("%H:%M:%S")
                self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                
                # Handle different message types
                if msg.type == 0:  # System/Event message
                    self.chat_text.insert(tk.END, f"{msg.text}\n", "system")
                else:
                    self.chat_text.insert(tk.END, f"{msg.sender.name}: ", "sender")
                    self.chat_text.insert(tk.END, f"{msg.text}\n", "message")
                    
            self.chat_text.configure(state=tk.DISABLED)
            self.chat_text.see(tk.END)
            
        except Exception as e:
            print(f"Error displaying messages: {e}")

def main():
    parser = argparse.ArgumentParser(description="F-Chat Viewer")
    parser.add_argument("--database", required=True, help="Path to the database directory")
    parser.add_argument("--character", required=True, help="Character name")
    parser.add_argument("--conversation", required=True, help="Conversation key")
    
    args = parser.parse_args()
    
    app = ChatViewer(args.database, args.character, args.conversation)
    app.mainloop()

if __name__ == "__main__":
    main()
