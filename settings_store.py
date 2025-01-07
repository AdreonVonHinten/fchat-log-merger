import os
import json
from typing import Dict, List, Optional, Any, TypeVar, Generic

K = TypeVar('K', bound=str)
V = TypeVar('V')

class SettingsKeys:
    """Type definitions for settings keys and their values"""
    pass

class SettingsStore(Generic[K, V]):
    def __init__(self, log_directory: str = "./examples/device_a/data"):
        self.log_directory = log_directory

    def get_settings_dir(self, character: Optional[str] = None) -> str:
        """Get the settings directory for a character"""
        dir_path = os.path.join(self.log_directory, character or "", "settings")
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    def get(self, key: K, character: Optional[str] = None) -> Optional[V]:
        """Get a setting value for a key and optional character"""
        try:
            file_path = os.path.join(self.get_settings_dir(character), key)
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"READ KEY FAILURE {e} {key} {character}")
            return None

    def get_available_characters(self) -> List[str]:
        """Get list of all characters with settings"""
        os.makedirs(self.log_directory, exist_ok=True)
        return [
            name for name in os.listdir(self.log_directory)
            if os.path.isdir(os.path.join(self.log_directory, name))
        ]

    def set(self, key: K, value: V) -> None:
        """Set a setting value for a key"""
        try:
            file_path = os.path.join(self.get_settings_dir(), key)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(value, f)
        except Exception as e:
            print(f"Error writing setting: {e}")
