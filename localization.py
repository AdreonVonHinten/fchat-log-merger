from typing import Dict

class Localization:
    def __init__(self):
        self._current_locale = "en"
        self._translations = {
            "en": {
                # Main window
                "app_title": "F-Chat Log Merger",
                "account_label": "Account",
                "settings_button": "⚙️ Settings",
                "available_databases": "Available Databases",
                "conversation_column": "Conversation",
                "data_a_column": "Data A",
                "data_b_column": "Data B",
                "merge_options": "Merge Options",
                "both_devices": "Both Databases",
                "device_a_only": "Database A Only",
                "device_b_only": "Database B Only",
                "view_selected": "View Selected",
                "merge_selected": "Merge Selected",
                
                # Context menu
                "view_conversation": "View Conversation",
                "merge_menu": "Merge",
                "merge_to_a": "Merge to Database A",
                "merge_to_b": "Merge to Database B",
                "merge_to_both": "Merge to Both",
                
                # Settings dialog
                "settings_title": "Database Settings",
                "data_folders": "Data-Folders",
                "device_a": "Database A:",
                "device_b": "Database B:",
                "browse_button": "Browse...",
                "save_button": "Save",
                "cancel_button": "Cancel",
                "settings_help": "Select the data-Folders of your F-Chat Rising Application.\nThis usually resides under C:/Users/<Username>/AppData/Roaming/fchat/data",
                
                # Diff viewer
                "diff_title": "Diff View - {account}/{conversation}",
                "data_a_frame": "Database A",
                "data_b_frame": "Database B",
                "prev_diff": "⬆ Previous",
                "next_diff": "⬇ Next",
                "change_blocks": "Change Blocks: {current}/{total}",
                
                # Messages
                "no_selection": "No Selection",
                "select_conversation": "Please select at least one conversation to merge",
                "merge_error": "Merge Error",
                "merge_error_msg": "Failed to merge conversation {conversation}: {error}",
                "merge_success": "Success",
                "merge_success_msg": "Successfully merged {count} conversation(s)",
                "load_error": "Error",
                "load_error_msg": "Failed to load databases: {error}",
                "select_paths": "Please select both database paths"
            }
            # Add other languages here
        }
        
    def set_locale(self, locale: str) -> None:
        """Set the current locale"""
        if locale in self._translations:
            self._current_locale = locale
            
    def get_text(self, key: str, **kwargs) -> str:
        """Get localized text for key with optional format arguments"""
        text = self._translations.get(self._current_locale, {}).get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text
        
# Global instance
L10N = Localization()
