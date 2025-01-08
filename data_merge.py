import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Set, Tuple
from fchat_logs import ChatLogs, Message, Character

@dataclass
class MergeConfig:
    """Configuration for merge operation"""
    account: str
    conversation: Tuple[str, str]
    device_a_path: str
    device_b_path: str
    target: str  # "both", "device_a", or "device_b"

class DataMerger:
    def __init__(self):
        self.backup_dir = os.path.join("backups", datetime.now().strftime("%Y%m%d_%H%M%S"))
        
    def merge_conversation(self, config: MergeConfig) -> None:
        """Merge conversation between devices"""
        db_a = ChatLogs(config.device_a_path)
        db_b = ChatLogs(config.device_b_path)

        # Create backups first
        if config.target in ["both", "device_a"]:
            self._backup_db(db_a, config.account, config.conversation[0], 'db_a')
        if config.target in ["both", "device_b"]:
            self._backup_db(db_b, config.account, config.conversation[0], 'db_b')

        # TODO get on a date by date basis to save on memory
        # Get messages from both devices
        messages_a = db_a.get_backlog(config.account, config.conversation[0])
        messages_b = db_b.get_backlog(config.account, config.conversation[0])
        
        # Create message maps with timestamps as keys for easy lookup
        map_a = {} if len(messages_a) == 0 else  {self._get_message_key(m): m for m in messages_a}
        map_b = {} if len(messages_b) == 0 else  {self._get_message_key(m): m for m in messages_b}
        
        # Get all unique timestamps
        all_keys = sorted(set(map_a.keys()) | set(map_b.keys()))
        
        # Create merged database
        merged_db = ChatLogs(os.path.join("temp", "merge"))
        merged_db.clear(config.account, config.conversation[0])
        
        # Add all messages to merged database
        for key in all_keys:
            msg = map_a.get(key) or map_b.get(key)
            merged_db.log_message(config.account, config.conversation, msg)
            
        merged_file = merged_db.get_log_file(config.account, config.conversation[0])
        merged_file_ix = merged_db.get_log_file_ix(config.account, config.conversation[0])
        
        # Save merged database to target(s)
        if config.target in ["both", "device_a"]:
            self._copy_and_replace(merged_file, db_a.get_log_file(config.account, config.conversation[0]))
            self._copy_and_replace(merged_file_ix, db_a.get_log_file_ix(config.account, config.conversation[0]))

        if config.target in ["both", "device_b"]:
            self._copy_and_replace(merged_file, db_b.get_log_file(config.account, config.conversation[0]))
            self._copy_and_replace(merged_file_ix, db_b.get_log_file_ix(config.account, config.conversation[0]))
        
    
    def _copy_and_replace(self, source_path, destination_path):
        if not os.path.exists(source_path):
            return
        if os.path.exists(destination_path):
            os.remove(destination_path)
        shutil.copy2(source_path, destination_path)

    def _backup_db(self, db : ChatLogs, account: str, conversation : str, prefix : str) -> None:
        log_file = db.get_log_file(account, conversation)
        if not os.path.exists(log_file):
            return
            
        backup_file = os.path.join(self.backup_dir, prefix, account, conversation)
        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        shutil.copy2(log_file, backup_file)

        log_file_ix = db.get_log_file_ix(account, conversation)
        if not os.path.exists(log_file):
            return
            
        backup_file = os.path.join(self.backup_dir, prefix, account, conversation + '.idx')
        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        shutil.copy2(log_file_ix, backup_file)
       
    def _get_message_key(self, msg: Message) -> Tuple:
        """Get unique key for message"""
        return (
            msg.time.timestamp(),
            msg.type,
            hash(msg.sender.name if msg.sender else ""),
            hash(msg.text)
        )
