import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from fchat_logs import ChatLogs
from localization import L10N

class DiffViewer(ttk.Toplevel):
    def __init__(self, parent, account: str, conversation: str, device_a_db: ChatLogs, device_b_db: ChatLogs):
        super().__init__(parent)
        self.title(L10N.get_text("diff_title", account=account, conversation=conversation))
        self.geometry("1200x800")
        
        # Store references
        self.account = account
        self.conversation = conversation
        self.device_a_db = device_a_db
        self.device_b_db = device_b_db
        self.diff_blocks = []  # Store start and end lines of diff blocks
        self.current_block = -1  # Current block index
        
        self._create_ui()
        self._load_diff()
        
    def _create_ui(self):
        """Create the diff view UI"""
        # Main container with padding
        main_container = ttk.Frame(self, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Navigation buttons at top
        nav_frame = ttk.Frame(main_container)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Previous difference button
        self.prev_btn = ttk.Button(
            nav_frame,
            text=L10N.get_text("prev_diff"),
            command=self._goto_prev_diff,
            style="info.Outline.TButton"
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        # Next difference button
        self.next_btn = ttk.Button(
            nav_frame,
            text=L10N.get_text("next_diff"),
            command=self._goto_next_diff,
            style="info.Outline.TButton"
        )
        self.next_btn.pack(side=tk.LEFT)
        
        # Difference counter
        self.diff_counter = ttk.Label(
            nav_frame,
            text=L10N.get_text("change_blocks", current=0, total=0),
            style="info.Inverse.TLabel"
        )
        self.diff_counter.pack(side=tk.LEFT, padx=10)
        
        # Create paned window for side-by-side view
        self.paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Create frame for text widgets and scrollbars
        text_frame = ttk.Frame(self.paned)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_columnconfigure(1, weight=0)  # Scrollbar column
        text_frame.grid_columnconfigure(2, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_rowconfigure(1, weight=0)  # Horizontal scrollbar row
        
        # Left side (Data A)
        left_frame = ttk.LabelFrame(text_frame, text=L10N.get_text("data_a_frame"), padding=5)
        left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_text = tk.Text(
            left_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#2b2b2b",
            fg="#ffffff",
            width=70
        )
        self.left_text.pack(fill=tk.BOTH, expand=True)
        
        # Right side (Data B)
        right_frame = ttk.LabelFrame(text_frame, text=L10N.get_text("data_b_frame"), padding=5)
        right_frame.grid(row=0, column=2, sticky="nsew")
        self.right_text = tk.Text(
            right_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#2b2b2b",
            fg="#ffffff",
            width=70
        )
        self.right_text.pack(fill=tk.BOTH, expand=True)
        
        # Shared vertical scrollbar
        self.scrollbar_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        
        # Shared horizontal scrollbar
        self.scrollbar_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        self.scrollbar_x.grid(row=1, column=0, columnspan=3, sticky="ew")
        
        # Configure scrollbar commands
        self.scrollbar_y.configure(command=self._on_vertical_scroll)
        self.scrollbar_x.configure(command=self._on_horizontal_scroll)
        
        # Configure text widget scrolling
        self.left_text.configure(
            yscrollcommand=self._on_left_scroll_y,
            xscrollcommand=self._on_left_scroll_x
        )
        self.right_text.configure(
            yscrollcommand=self._on_right_scroll_y,
            xscrollcommand=self._on_right_scroll_x
        )
        
        # Add frame to paned window
        self.paned.add(text_frame, weight=1)
        
        # Configure tags for highlighting
        self.left_text.tag_configure("different", background="#4a3030")
        self.right_text.tag_configure("different", background="#4a3030")
        self.left_text.tag_configure("gap", foreground="#666666", background="#1f1f1f")
        self.right_text.tag_configure("gap", foreground="#666666", background="#1f1f1f")
        self.left_text.tag_configure("current_diff", background="#6a4040")
        self.right_text.tag_configure("current_diff", background="#6a4040")
        
        # Bind mouse wheel events for synchronized scrolling
        self.left_text.bind("<MouseWheel>", self._on_mousewheel)
        self.right_text.bind("<MouseWheel>", self._on_mousewheel)
        
        # Bind keyboard shortcuts
        self.bind("<Alt-Up>", lambda e: self._goto_prev_diff())
        self.bind("<Alt-Down>", lambda e: self._goto_next_diff())
        
    def _on_vertical_scroll(self, *args):
        """Sync vertical scrolling between both text widgets"""
        self.left_text.yview(*args)
        self.right_text.yview(*args)
        
    def _on_horizontal_scroll(self, *args):
        """Sync horizontal scrolling between both text widgets"""
        self.left_text.xview(*args)
        self.right_text.xview(*args)
        
    def _on_left_scroll_y(self, first, last):
        """Handle left text vertical scroll"""
        self.scrollbar_y.set(first, last)
        self.right_text.yview_moveto(first)
        
    def _on_right_scroll_y(self, first, last):
        """Handle right text vertical scroll"""
        self.scrollbar_y.set(first, last)
        self.left_text.yview_moveto(first)
        
    def _on_left_scroll_x(self, first, last):
        """Handle left text horizontal scroll"""
        self.scrollbar_x.set(first, last)
        self.right_text.xview_moveto(first)
        
    def _on_right_scroll_x(self, first, last):
        """Handle right text horizontal scroll"""
        self.scrollbar_x.set(first, last)
        self.left_text.xview_moveto(first)
        
    def _on_mousewheel(self, event):
        """Handle mousewheel events for both text widgets"""
        self.left_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.right_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"  # Prevent default scrolling
        
    def _goto_prev_diff(self):
        """Jump to previous difference"""
        if not self.diff_blocks:
            return
            
        self.current_block = (self.current_block - 1) % len(self.diff_blocks)
        self._highlight_current_diff()
        
    def _goto_next_diff(self):
        """Jump to next difference"""
        if not self.diff_blocks:
            return
            
        self.current_block = (self.current_block + 1) % len(self.diff_blocks)
        self._highlight_current_diff()
        
    def _highlight_current_diff(self):
        """Highlight the current difference block and scroll to it"""
        # Remove previous current diff highlighting
        self.left_text.tag_remove("current_diff", "1.0", "end")
        self.right_text.tag_remove("current_diff", "1.0", "end")
        
        if not self.diff_blocks:
            return
            
        # Get current block position
        start_line, end_line = self.diff_blocks[self.current_block]
        
        # Add highlighting to the entire block
        self.left_text.tag_add("current_diff", f"{start_line}.0", f"{end_line + 1}.0")
        self.right_text.tag_add("current_diff", f"{start_line}.0", f"{end_line + 1}.0")
        
        # Scroll to make current diff visible
        self.left_text.see(f"{start_line}.0")
        self.right_text.see(f"{start_line}.0")
        
        # Update counter
        self.diff_counter.configure(
            text=L10N.get_text("change_blocks", current=self.current_block + 1, total=len(self.diff_blocks))
        )
        
    def _load_diff(self):
        """Load and display the diff between devices"""
        # Get messages from both devices
        messages_a = self.device_a_db.get_backlog(self.account, self.conversation)
        messages_b = self.device_b_db.get_backlog(self.account, self.conversation)
        
        # Format messages for display
        def format_message(msg):
            sender = msg.sender.name if msg.sender else "System"
            text = msg.text.split('\n')[0]  # Get first line only
            if len(text) > 80:
                text = text[:77] + "..."
            return f"{msg.time.strftime('%Y-%m-%d %H:%M:%S')} | {sender}: {text}"
        
        # Create message maps with timestamps as keys for easy lookup
        map_a = {(m.time.timestamp(), m.type, m.sender.name if m.sender else "", m.text): m for m in messages_a}
        map_b = {(m.time.timestamp(), m.type, m.sender.name if m.sender else "", m.text): m for m in messages_b}
        
        # Get all unique timestamps
        all_keys = sorted(set(map_a.keys()) | set(map_b.keys()))
        
        # Clear existing text and differences
        self.left_text.configure(state="normal")
        self.right_text.configure(state="normal")
        self.left_text.delete("1.0", "end")
        self.right_text.delete("1.0", "end")
        self.diff_blocks = []
        self.current_block = -1
        
        # Display messages with gaps
        line_number = 1
        block_start = None
        last_a = False
        last_b = False
        
        def end_block():
            nonlocal block_start
            if block_start is not None:
                self.diff_blocks.append((block_start, line_number - 1))
                block_start = None
        
        for key in all_keys:
            msg_a = map_a.get(key)
            msg_b = map_b.get(key)

            is_diff = (last_a != bool(msg_a)) or (last_b != bool(msg_b))
            last_a = bool(msg_a)
            last_b = bool(msg_b)
            
            # Handle block start/end
            if is_diff:
                if block_start is None:
                    block_start = line_number
            else:
                end_block()
            
            # Format lines with padding for missing messages
            if msg_a:
                self.left_text.insert("end", format_message(msg_a) + "\n", 
                                    "different" if not msg_b else "")
            else:
                self.left_text.insert("end", "" * 80 + "\n", "gap")
                
            if msg_b:
                self.right_text.insert("end", format_message(msg_b) + "\n",
                                     "different" if not msg_a else "")
            else:
                self.right_text.insert("end", "" * 80 + "\n", "gap")
                
            line_number += 1
        
        # Handle last block if it's still open
        end_block()
        
        # Make text widgets read-only
        self.left_text.configure(state="disabled")
        self.right_text.configure(state="disabled")
        
        # Update difference counter
        self.diff_counter.configure(text=L10N.get_text("change_blocks", current=0, total=len(self.diff_blocks)))
