# F-Chat Log Merger

A tool to merge F-Chat logs from multiple devices into a single database. Perfect for keeping your spicy conversations in sync! 🔥

## Features

- 🔄 Merge chat logs from two F-Chat databases
- 👀 View differences between conversations across devices
- 🎯 Selective merging (to Device A, Device B, or both)
- 🔍 Visual diff viewer for comparing conversations
- 🛡️ Automatic backups before merging
- 🌐 Support for all F-Chat message types
- 🎨 Modern, user-friendly interface
- 🌍 Localization support

## Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/f-chat-log-merge.git
cd f-chat-log-merge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Launch the application:
```bash
python main_view.py
```

2. Click the ⚙️ Settings button to configure your F-Chat data folders
3. Select an account from the dropdown
4. Choose conversations to merge:
   - Red items indicate different content between devices
   - Gray items are identical
5. Select your merge target (Device A, Device B, or Both)
6. Click "Merge Selected" to merge the conversations

## Development

### Project Structure

- `main_view.py` - Main UI and application entry point
- `data_merge.py` - Core merge logic and database operations
- `fchat_logs.py` - F-Chat database interaction
- `settings_dialog.py` - Configuration dialog
- `localization.py` - Text localization support
- `test_db_integrity.py` - Database integrity testing tool

### Testing

Use the database integrity testing tool to verify read/write operations:

```bash
python test_db_integrity.py -s <source_path> -a <account> -c <conversation>
```

Or use the VS Code launch configuration "Test DB Integrity".

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
