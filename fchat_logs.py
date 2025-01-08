from cgitb import handler
import imp
import os
import shutil
import struct
import argparse
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from datetime import datetime
from dateutil.tz import tzlocal 
from enum import Enum

DAY_MS = 24 * 60 * 60 * 1000  # milliseconds in a day
LOCAL_TZ = tzlocal()

@dataclass
class Character:
    name: str
    gender: str = "None"
    status: str = "online"
    status_text: str = ""
    is_friend: bool = False
    is_bookmarked: bool = False
    is_chat_op: bool = False
    is_ignored: bool = False
    overrides: Dict[str, Any] = None

    def __post_init__(self):
        if self.overrides is None:
            self.overrides = {}

class MessageType(Enum):
    Message = 0
    Action = 1
    Ad = 2
    Roll = 3
    Warn = 4
    Event = 5
    Bcast = 6

@dataclass
class Message:
    time: datetime
    type: MessageType
    sender: Character
    text: str

@dataclass
class IndexItem:
    name: str
    index: Dict[int, int]  # day timestamp -> offset index
    offsets: List[int]     # actual file offsets

class ChatLogs:
    def __init__(self, log_directory):
        self.log_directory = log_directory
        self.index: Dict[str, IndexItem] = {}
        self.loaded_index: Optional[Dict[str, IndexItem]] = None
        self.loaded_character: Optional[str] = None

    def get_log_dir(self, character: str) -> str:
        """Get the logs directory for a character"""
        dir_path = os.path.join(self.log_directory, character, "logs")
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    def get_log_file(self, character: str, key: str) -> str:
        """Get the full path to a log file"""
        return os.path.join(self.get_log_dir(character), key)

    def get_log_file_ix(self, character: str, key: str) -> str:
        """Get the full path to a log file"""
        return os.path.join(self.get_log_dir(character), key + '.idx')

    def clear(self, character: str, key: str) -> str:
        log_file = self.get_log_file(character, key)
        if os.path.exists(log_file):
            os.remove(log_file)
        log_file_ix = self.get_log_file_ix(character, key)
        if os.path.exists(log_file_ix):
            os.remove(self.get_log_file_ix(character, key))

    def serialize_message(self, message: Message) -> Tuple[bytes, int]:
        """Serialize a message to bytes"""
        name = "" if message.type == MessageType.Event else message.sender.name 
        name_bytes = name.encode('utf-8')
        text_bytes = message.text.encode('utf-8')
        
        # Calculate sizes
        name_len = len(name_bytes)
        text_len = len(text_bytes)
        total_size = name_len + text_len + 10  # 4(time) + 1(type) + 1(name_len) + 2(text_len) + 2(total_size)
        
        # Create buffer
        buffer = bytearray(total_size)
        
        # Write data
        struct.pack_into('<I', buffer, 0, int(message.time.timestamp()))  # 4 bytes timestamp
        buffer[4] = message.type  # 1 byte type
        buffer[5] = name_len  # 1 byte name length
        buffer[6:6+name_len] = name_bytes  # name
        struct.pack_into('<H', buffer, 6+name_len, text_len)  # 2 bytes text length
        buffer[8+name_len:8+name_len+text_len] = text_bytes  # text
        struct.pack_into('<H', buffer, 8+name_len+text_len, total_size-2)  # 2 bytes total size at end
        
        return bytes(buffer), total_size

    def deserialize_message(self, buffer: bytes, offset: int = 0) -> Tuple[Message, int]:
        """Deserialize a message from bytes"""
        # read meta data
        timestamp = struct.unpack_from('<I', buffer, offset)[0]
        msg_type = buffer[offset + 4]
        name_len = buffer[offset + 5]
        curr_offset = offset + 6

        # read sender name
        name_bytes =  buffer[curr_offset:curr_offset + name_len]
        sender_name = name_bytes.decode('utf-8')
        curr_offset += name_len
        
        # read message
        text_len = struct.unpack_from('<H', buffer, curr_offset)[0]
        curr_offset += 2
        text = buffer[curr_offset:curr_offset + text_len].decode('utf-8')
        curr_offset += text_len
        
        # Verify size marker at end
        size_marker = struct.unpack_from('<H', buffer, curr_offset)[0]
        if size_marker != curr_offset - offset:
            raise ValueError("Invalid message size marker")
            
        return Message(
            time=datetime.fromtimestamp(timestamp, LOCAL_TZ),
            type=msg_type,
            sender=Character(name=sender_name),
            text=text
            # 6 bytes prefix,  2 bytes text_length, 2 bytes size_marker
        ), name_len + text_len + 10  

    def check_index(self, message: Message, key: str, name: str, size: int) -> Optional[bytes]:
        """Update index for a new message and return bytes to write to index file"""
        utc_offset_seconds = 0 if message.time.utcoffset() is None else message.time.utcoffset().total_seconds()
        date = int(message.time.timestamp() * 1000 / DAY_MS - utc_offset_seconds / 60 / 1440)
        
        item = self.index.get(key)
        if item is not None:
            # we already have an offset stored for this date
            if date in item.index:
                return None
            buffer = bytearray(7)
            offset = 0
        else:
            # no index file exists for this conversation, we create a new one
            self.index[key] = item = IndexItem(name=name, index={}, offsets=[])
            name_bytes = name.encode('utf-8')
            name_len = len(name_bytes)
            # we initially create a buffer that contains
            # - 1 byte for name length
            # - x bytes for the name
            # - 2 bytes for the date
            # - 5 bytes for the file offset
            buffer = bytearray(name_len + 8)
            # fill name length and name into the buffer
            buffer[0] = name_len
            buffer[1:1+name_len] = name_bytes
            offset = name_len + 1
        
        # update programs index-file
        item.index[date] = len(item.offsets)
        item.offsets.append(size)

        # write date
        struct.pack_into('<H', buffer, offset, date)
        offset += 2
        # Pack 5-byte integer for file offset
        value_5_bytes = size.to_bytes(5, byteorder='little')
        buffer[offset:offset+5] = value_5_bytes

        return bytes(buffer)

    def get_index(self, name: str) -> Dict[str, IndexItem]:
        """Load index for a character"""
        if self.loaded_character == name:
            return self.index or {}
            
        self.loaded_character = name
        self.index = {}
        
        dir_path = self.get_log_dir(name)
        try:
            for file in os.listdir(dir_path):
                if not file.endswith('.idx'):
                    continue
                    
                with open(os.path.join(dir_path, file), 'rb') as f:
                    content = f.read()
                    name_len = content[0]
                    offset = name_len + 1
                    
                    item = IndexItem(
                        name=content[1:offset].decode('utf-8'),
                        index={},
                        offsets=[]
                    )
                    
                    while offset < len(content):
                        day = struct.unpack_from('<H', content, offset)[0]
                        file_offset = sum(content[offset+2+i] << (i*8) for i in range(5))
                        item.index[day] = len(item.offsets)
                        item.offsets.append(file_offset)
                        offset += 7
                        
                    self.index[file[:-4].lower()] = item
                    
        except Exception as e:
            print(f"Error loading index: {e}")
            
        return self.index


    def validate_msg_size(self, buffer : bytes, offset : int, size_marker : int) -> bool:
        # append name length to offset (skip timestamp and msg_type)
        curr_offset = offset + 6 + buffer[offset + 5]
        text_len = struct.unpack_from('<H', buffer, curr_offset)[0]
        # add text-length bytes (2) plus actual text-length
        curr_offset += 2 + text_len
        return size_marker == curr_offset - offset

    def get_backlog_size(self, character: str, conversation_key: str) -> List[Message]:
        # handler that only reads the size (for validity) and counts
        def _size_handler(buffer: bytes, offset : int, result : int = None) -> Tuple[int, bool] :
            # initialize result
            if result is None:
                result = 0
            # append name length to offset (skip timestamp and msg_type)
            curr_offset = offset + 6 + buffer[offset + 5]
            text_len = struct.unpack_from('<H', buffer, curr_offset)[0]
            # add text-length bytes (2) plus actual text-length
            curr_offset += 2 + text_len

            return result + 1, True

        # read through backlog using handler
        result = self._read_backlog(character, conversation_key, _size_handler)
        return 0 if result is None else result

    def get_log_dates(self, character: str, conversation_key: str) -> List[datetime]:
        def _date_handler(buffer : bytes, offset : int, result : List[datetime] = None) -> Tuple[List[datetime], bool]:
            # initialize result
            if result is None:
                result = list()
            
            # timestamp in millis (without timezone data)
            timestamp = struct.unpack_from('<I', buffer, offset)[0]
            new_date = datetime.fromtimestamp(timestamp, LOCAL_TZ)
            if len(result) == 0 or (result[0] - new_date).days != 0:
                result.insert(0, new_date)
            return result, True
        
        # read through backlog using handler
        result = self._read_backlog(character, conversation_key, _date_handler)
        return [] if result is None else result

    def get_backlog(self, character: str, conversation_key: str, count: int = -1, date: datetime = None) -> List[Message]:
        def _msg_handler(buffer : bytes, offset : int, result: List[Message] = None):
            if result is None:
                result = list()

            # if date is present check it first
            if not date is None:
                timestamp = struct.unpack_from('<I', buffer, offset)[0]
                msg_date = datetime.fromtimestamp(timestamp, LOCAL_TZ)
                days_delta = (msg_date - date).days
                # skip iteration if message is from another date
                if days_delta != 0:
                    # return the list and only proceed if the msg_date is bigger than the filter_date
                    return result, days_delta > 0
                  
            # read message and add to results
            msg, _ = self.deserialize_message(buffer, offset)
            result.insert(0, msg)
            # return messages and continue as long as count is not satisfied
            return result, count == -1 or len(result) < count
        result = self._read_backlog(character, conversation_key, _msg_handler)
        return [] if result is None else result

    def _read_backlog(self, character: str, conversation_key: str, handler : Callable) -> any:
        """Read through a log file backwards, processing messages with the given handler
        
        Args:
            character: Character name
            conversation_key: Conversation identifier
            handler: Callback function(buffer, offset, result) -> (new_result, continue_reading)
        
        Returns:
            The final result from the handler, or None if an error occurred
        """
        file_path = self.get_log_file(character, conversation_key)
        if not os.path.exists(file_path):
            return None
            
        result = None
        try:
            with open(file_path, 'rb') as f:
                chunk_size = 65536
                buffer = bytearray(chunk_size)
                pos = os.path.getsize(file_path)
                while pos > 0:
                    # Read a chunk from the end of the file
                    read_size = min(chunk_size, pos)
                    pos -= read_size
                    f.seek(pos)
                    f.readinto(buffer)
                    
                    # Process chunk from end to start
                    offset = read_size
                    # we need at least 2 byte for a size-marker
                    while offset >= 2:
                        # Find message boundary by looking for size marker
                        # we are reading the messages backwards so we check the last two bytes for the current messages size to find the start of it
                        size_marker = struct.unpack_from('<H', buffer, offset - 2)[0]
                        msg_offset = (size_marker + 2)
                        # break if past buffer-boundary
                        if (offset - msg_offset) < 0:
                            break
                        # jump back
                        offset -= msg_offset
                        # first validate msg size for integrity
                        if not self.validate_msg_size(buffer, offset, size_marker):
                            raise ValueError("msg_size and size_marker mismatch")
                        # read actual data
                        result, do_continue = handler(buffer, offset, result)
                        if not do_continue:
                            return result
                    # correct pos by remaining offset
                    pos += offset     
                # end of while pos > 0
            # end of with open(file_path...    
            return result
            
        except Exception as e:
            print(f"Error reading backlog of file {file_path}: {e}")
            return None
    
    def get_conversations(self, character: str) -> List[Tuple[str, str]]:
        """Get list of all conversations for a character"""
        index = self.get_index(character)
        return [(key, item.name) for key, item in index.items()]

    def get_available_characters(self) -> List[str]:
        """Get list of all characters with logs"""
        os.makedirs(self.log_directory, exist_ok=True)
        return [
            name for name in os.listdir(self.log_directory)
            if os.path.isdir(os.path.join(self.log_directory, name))
        ]

    def fix_logs(self, character: str) -> None:
        """Fix corrupted log files and their indices"""
        dir_path = self.get_log_dir(character)
        files = os.listdir(dir_path)
        buffer = bytearray(50100)
        
        for file in files:
            full_path = os.path.join(dir_path, file)
            
            # Handle index files
            if file.endswith('.idx'):
                log_path = full_path[:-4]  # Remove .idx
                if not os.path.exists(log_path):
                    os.unlink(full_path)
                continue
                
            # Open log file
            try:
                with open(full_path, 'rb+') as fd:
                    index_path = f"{full_path}.idx"
                    if not os.path.exists(index_path):
                        os.unlink(full_path)
                        continue
                        
                    with open(index_path, 'rb+') as index_fd:
                        # Read name length and content
                        index_fd.readinto(memoryview(buffer)[:1])
                        pos = 0
                        last_day = 0
                        name_end = buffer[0] + 1
                        
                        # Truncate index to name section
                        index_fd.truncate(name_end)
                        index_fd.seek(0)
                        index_fd.readinto(memoryview(buffer)[:name_end])
                        
                        # Get file size
                        fd.seek(0, os.SEEK_END)
                        size = fd.tell()
                        
                        try:
                            while pos < size:
                                buffer[50100:] = [-1] * (len(buffer) - 50100)
                                fd.seek(pos)
                                fd.readinto(memoryview(buffer)[:50100])
                                
                                # Create dummy character for deserialization
                                def char_getter(name: str) -> Character:
                                    return Character(name=name)
                                
                                msg, msg_size = self.deserialize_message(buffer, 0)
                                time = msg.time
                                day = int(time.timestamp() * 1000 / DAY_MS - time.utcoffset().total_seconds() / 60 / 1440)
                                
                                if day > last_day:
                                    # Write new index entry
                                    struct.pack_into('<H', buffer, 0, day)
                                    for i in range(5):
                                        buffer[2 + i] = (pos >> (i * 8)) & 0xFF
                                    index_fd.write(buffer[:7])
                                    last_day = day
                                
                                # Verify message size marker
                                if struct.unpack_from('<H', buffer, msg_size - 2)[0] != msg_size - 2:
                                    raise ValueError("Invalid message size marker")
                                    
                                pos += msg_size
                                
                        except Exception as e:
                            print(f"Error fixing log {file}: {e}")
                            fd.truncate(pos)
                            
            except Exception as e:
                print(f"Error opening files for {file}: {e}")
                continue

    def log_message(self, account, conversation, messages: Union[Message, List[Message]]) -> None:
        """Write one or multiple messages to the log file
        
        Args:
            conversation: Dict with 'key' and 'name' of the conversation
            messages: Single message or list of messages to write
        """
        file_path = self.get_log_file(account, conversation[0])
        
        # Convert single message to list
        if not isinstance(messages, list):
            messages = [messages]
            
        # Get current file size for index
        current_size = os.path.exists(file_path) and os.path.getsize(file_path) or 0
        # Process all messages
        for message in messages:
            # Serialize message
            buffer, _ = self.serialize_message(message)
            index = self.get_index(account)
            # Check and update index
            has_index = conversation[0] in index
            index_buffer = self.check_index(
                message, 
                conversation[0], 
                conversation[1],
                current_size
            )
            
            # Write index if needed
            if index_buffer is not None:
                index_path = f"{file_path}.idx"
                # 'a' to append if exists, 'wx' to create new if doesn't exist
                with open(index_path, 'ab' if has_index else 'xb') as f:
                    f.write(index_buffer)
            
            # Write message
            with open(file_path, 'ab') as f:
                f.write(buffer)
                
            # Update size for next message
            current_size += len(buffer)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F-Chat Database Inspector ")
    parser.add_argument('-a', '--account', help='Account to get Logfiles for')
    parser.add_argument('-c', '--conversation',  help='Conversation to read from')
    parser.add_argument('-d', '--dump', type=int, help='Dump contents of a specific log entry (0-based index)')
    
    args = parser.parse_args()
    
    if not args.account:
        parser.error("Please specify an account name with -a")
        exit
        
    chat_logs = ChatLogs()
    if not args.conversation:
        conversations = chat_logs.get_conversations(args.account) 
        for conversation in conversations:
            print(conversation)
        exit
    
    messages = chat_logs.get_backlog(args.account, args.conversation)
    for message in messages:
        print(message)
    exit