# F-Chat Log Merge Tool 🔄

A powerful tool for merging F-Chat logs from multiple devices with an intuitive graphical interface. Compare and merge your chat histories while maintaining data integrity and avoiding duplicates.

## Features ✨

- **Visual Log Comparison**
  - Side-by-side diff view of chat logs
  - Highlights differences between device logs
  - Navigate through changes with keyboard shortcuts
  - Synchronized scrolling for easy comparison

- **Smart Merging**
  - Detects and removes duplicate messages
  - Preserves message timestamps and sender information
  - Automatic backup creation before merging
  - Support for multiple target devices

- **User-Friendly Interface**
  - Account and conversation selection
  - Visual indicators for different log states
  - Progress tracking during merge operations
  - Dark theme for comfortable viewing

## Installation 🚀

1. Clone the repository:
```bash
git clone https://github.com/AdreonVonHinten/fchat-log-merger.git
cd fchat-log-merger
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage 💫

1. Launch the merge tool:
```bash
python merge_tool.py --database /path/to/your/database
```

2. Select an account from the dropdown menu

3. The tool will display available conversations with their status:
   - 🔴 Red: Different content between devices
   - ⚪ Gray: Same content on both devices

4. To compare logs:
   - Right-click a conversation
   - Select "View Conversation"
   - Use Alt+Up/Down to navigate between differences
   - Use the mouse wheel or scrollbar to scroll both views simultaneously

5. To merge logs:
   - Select the conversations you want to merge
   - Choose your target device(s)
   - Click "Merge Selected"
   - Backups will be automatically created in the `backups` directory

## Directory Structure 📁

```
F-Chat-Log-Merge/
├── merge_tool.py     # Main application
├── chat_viewer.py    # Chat log viewer
├── diff_viewer.py    # Diff view implementation
├── fchat_logs.py     # F-Chat log handling
├── examples/         # Example data for testing
├── backups/         # Automatic backups
├── temp/            # Temporary merge files
└── merge/           # Merged output files
```

## Keyboard Shortcuts ⌨️

- `Alt + Up`: Navigate to previous difference
- `Alt + Down`: Navigate to next difference
- `Mouse Wheel`: Scroll both diff views simultaneously

## Contributing 🤝

Contributions are welcome! Please feel free to submit pull requests or open issues for any bugs or feature requests.

## License 📜

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- Built with Python and tkinter/ttkbootstrap
- Special thanks to the F-Chat community
