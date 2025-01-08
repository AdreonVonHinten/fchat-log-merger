import os
from fchat_logs import ChatLogs, Message
from typing import Tuple, Optional
import shutil
import argparse

def compare_files(file1: str, file2: str) -> Optional[Tuple[int, bytes, bytes]]:
    """
    Compare two files byte by byte.
    Returns (offset, byte1, byte2) of first difference, or None if files are identical.
    """
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        # Read files in chunks for memory efficiency
        chunk_size = 8192
        offset = 0
        
        while True:
            chunk1 = f1.read(chunk_size)
            chunk2 = f2.read(chunk_size)
            
            # Check if we've reached the end of both files
            if not chunk1 and not chunk2:
                return None
                
            # Check if files have different lengths
            if len(chunk1) != len(chunk2):
                shorter_len = min(len(chunk1), len(chunk2))
                # First check the common part
                for i in range(shorter_len):
                    if chunk1[i] != chunk2[i]:
                        return offset + i, chunk1[i:i+1], chunk2[i:i+1]
                # If common part is identical, difference is in length
                return offset + shorter_len, \
                       (chunk1[shorter_len:shorter_len+1] if len(chunk1) > len(chunk2) else b'\x00'), \
                       (chunk2[shorter_len:shorter_len+1] if len(chunk2) > len(chunk1) else b'\x00')
            
            # Compare chunks
            for i in range(len(chunk1)):
                if chunk1[i] != chunk2[i]:
                    return offset + i, chunk1[i:i+1], chunk2[i:i+1]
            
            offset += len(chunk1)

def test_database_integrity(source_db_path: str, test_account: str, test_conversation: str) -> None:
    """
    Test database read/write integrity by:
    1. Reading messages from source database
    2. Writing them to a new test database
    3. Comparing the files byte by byte
    """
    # Create test directory
    test_dir = "test_db"
    os.makedirs(test_dir, exist_ok=True)
    
    # Copy source database to test directory to ensure we have all necessary files
    test_db_path = os.path.join(test_dir, "test.db")
    shutil.copytree(source_db_path, test_db_path, dirs_exist_ok=True)
 
    # Open source database
    source_db = ChatLogs(source_db_path)
    index = source_db.get_index(test_account)
    if not index[test_conversation]:
        print(f"No index found for {test_account}/{test_conversation}")
        return

    conversation_name = index[test_conversation].name
    # Read all messages from source
    messages = source_db.get_backlog(test_account, test_conversation)
    if not messages:
        print(f"No messages found for {test_account}/{test_conversation}")
        return
        
    print(f"Read {len(messages)} messages from source database")
    
    # Create fresh test database
    shutil.rmtree(test_db_path)
    os.makedirs(test_db_path)
    test_db = ChatLogs(test_db_path)
    
    # Write messages to test database
    for msg in messages:
        test_db.log_message(test_account, [test_conversation, conversation_name], msg)

    # Compare log files
    source_log = source_db.get_log_file(test_account, test_conversation)
    test_log =  test_db.get_log_file(test_account, test_conversation)

    print("\nComparing log files...")
    diff = compare_files(source_log, test_log)
    if diff:
        offset, byte1, byte2 = diff
        print(f"First difference found at offset: {offset} (0x{offset:X})")
        print(f"Source byte: {int.from_bytes(byte1, 'big'):02X} ({int.from_bytes(byte1, 'big')})")
        print(f"Test byte:   {int.from_bytes(byte2, 'big'):02X} ({int.from_bytes(byte2, 'big')})")
    else:
        print("Log files are identical! 🎉")
        
    # Compare index files
    source_idx = source_db.get_log_file_ix(test_account, test_conversation)
    test_idx = test_db.get_log_file_ix(test_account, test_conversation)
    
    print("\nComparing index files...")
    diff = compare_files(source_idx, test_idx)
    if diff:
        offset, byte1, byte2 = diff
        print(f"First difference found at offset: {offset} (0x{offset:X})")
        print(f"Source byte: {int.from_bytes(byte1, 'big'):02X} ({int.from_bytes(byte1, 'big')})")
        print(f"Test byte:   {int.from_bytes(byte2, 'big'):02X} ({int.from_bytes(byte2, 'big')})")
    else:
        print("Index files are identical! 🎉")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F-Chat Database Inspector ")
    parser.add_argument('-s', '--source', help='Source-Path')
    parser.add_argument('-a', '--account', help='Account to get Logfiles for')
    parser.add_argument('-c', '--conversation', help='Conversation to get Logfiles for')
    
    args = parser.parse_args()
    

    if not args.account:
        parser.error("Please specify an account name with -a")
        
    if not args.conversation:
        parser.error("Please specify an account name with -c")

    test_database_integrity(
        args.source,
        args.account,  # Replace with actual account
        args.conversation  # Replace with actual conversation key
    )
