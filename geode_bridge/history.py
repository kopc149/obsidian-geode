# geode_bridge/history.py

import json
import logging
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import time  # <--- THE MISSING IMPORT IS ADDED HERE

from PyQt6.QtCore import QMutex, QMutexLocker
from .exceptions import FileOperationError

logger = logging.getLogger(__name__)

# --- ChatMessage and ChatSession dataclasses (Unchanged) ---
@dataclass
class ChatMessage:
    timestamp: str; sender: str; content: str; message_type: str = "text"
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage': return cls(**data)

@dataclass
class ChatSession:
    session_id: str; title: str; created_at: str; updated_at: str; messages: List[ChatMessage]
    def to_dict(self) -> Dict[str, Any]:
        return {'session_id': self.session_id, 'title': self.title, 'created_at': self.created_at, 'updated_at': self.updated_at, 'messages': [msg.to_dict() for msg in self.messages]}
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSession':
        messages = [ChatMessage.from_dict(msg) for msg in data.get('messages', [])]
        return cls(session_id=data['session_id'], title=data['title'], created_at=data['created_at'], updated_at=data['updated_at'], messages=messages)

class ChatHistoryManager:
    """Manages the lifecycle of all chat sessions, including saving and loading."""
    def __init__(self, history_file: str, max_sessions: int = 50):
        self.history_file = Path(history_file)
        self.max_sessions = max_sessions
        self.sessions: Dict[str, ChatSession] = {}
        self._file_mutex = QMutex()
        self.load_history()

    def create_session(self, title: str = None) -> ChatSession:
        session_id = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        timestamp = datetime.now().isoformat()
        if not title: title = f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        session = ChatSession(session_id=session_id, title=title, created_at=timestamp, updated_at=timestamp, messages=[])
        self.sessions[session_id] = session
        self.save_history(); logger.info(f"Created new chat session: {title} ({session_id})"); return session

    def add_message(self, session_id: str, sender: str, content: str, message_type: str = "text"):
        session = self.get_session(session_id)
        if not session: logger.warning(f"Attempted to add message to non-existent session: {session_id}"); return
        message = ChatMessage(timestamp=datetime.now().isoformat(), sender=sender, content=content, message_type=message_type)
        session.messages.append(message); session.updated_at = datetime.now().isoformat(); self.save_history()

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self.sessions.get(session_id)

    def get_recent_sessions(self, limit: int = 20) -> List[ChatSession]:
        return sorted(self.sessions.values(), key=lambda s: s.updated_at, reverse=True)[:limit]

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]; self.save_history(); logger.info(f"Deleted session: {session_id}"); return True
        logger.warning(f"Attempted to delete non-existent session: {session_id}"); return False

    def load_history(self):
        """Thread-safe loading of all chat sessions from the JSON file."""
        with QMutexLocker(self._file_mutex):
            if not self.history_file.exists():
                logger.info("Chat history file not found. A new one will be created on the first save.")
                return

            if self.history_file.stat().st_size == 0:
                logger.warning("Chat history file is empty. Starting fresh.")
                return

            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'sessions' not in data or not isinstance(data['sessions'], list):
                    logger.warning("Chat history file has invalid format. Starting fresh.")
                    self.sessions = {}; return
                
                for session_data in data.get('sessions', []):
                    session = ChatSession.from_dict(session_data)
                    self.sessions[session.session_id] = session
                logger.info(f"Loaded {len(self.sessions)} chat sessions from {self.history_file}")

            except json.JSONDecodeError:
                logger.error(f"Could not parse chat history file. Backing up and starting fresh.", exc_info=True)
                corrupted_backup_path = self.history_file.with_suffix(f".corrupted.{int(time.time())}.json")
                try: self.history_file.rename(corrupted_backup_path)
                except OSError as e: logger.error(f"Could not rename corrupted history file: {e}")
                self.sessions = {}
            except Exception as e:
                logger.error(f"An unexpected error occurred while loading chat history: {e}", exc_info=True)
                self.sessions = {}

    def save_history(self):
        """Thread-safe and atomic saving of all chat sessions to the JSON file."""
        with QMutexLocker(self._file_mutex):
            try:
                if len(self.sessions) > self.max_sessions:
                    sorted_sessions = sorted(self.sessions.values(), key=lambda s: s.updated_at, reverse=True)
                    self.sessions = {s.session_id: s for s in sorted_sessions[:self.max_sessions]}
                
                data = {'sessions': [session.to_dict() for session in self.sessions.values()]}
                
                temp_file = self.history_file.with_suffix(".tmp")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                temp_file.rename(self.history_file)
            except Exception as e:
                logger.error(f"Failed to save chat history: {e}", exc_info=True)