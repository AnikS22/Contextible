"""
Conversation Logger - Captures and stores AI conversations
This service logs all requests and responses going through ContextVault's proxy
"""

import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path

from ..database import get_db_context


@dataclass
class ConversationMessage:
    """A single message in a conversation."""
    id: str
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float
    metadata: Dict[str, Any]


@dataclass
class Conversation:
    """A complete conversation between user and AI."""
    id: str
    model_id: str
    start_time: float
    end_time: Optional[float]
    message_count: int
    messages: List[ConversationMessage]
    metadata: Dict[str, Any]


class ConversationLogger:
    """Logs and manages AI conversations for context extraction."""
    
    def __init__(self):
        self.active_conversations: Dict[str, Conversation] = {}
        self.conversation_db_path = Path("./conversations.db")
        self._init_conversation_db()
    
    def _init_conversation_db(self):
        """Initialize the conversation database."""
        try:
            conn = sqlite3.connect(self.conversation_db_path)
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    message_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not initialize conversation database: {e}")
    
    def start_conversation(self, model_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new conversation."""
        conversation_id = str(uuid.uuid4())
        
        conversation = Conversation(
            id=conversation_id,
            model_id=model_id,
            start_time=time.time(),
            end_time=None,
            message_count=0,
            messages=[],
            metadata=metadata or {}
        )
        
        self.active_conversations[conversation_id] = conversation
        
        # Save to database
        self._save_conversation_to_db(conversation)
        
        return conversation_id
    
    def log_user_message(self, conversation_id: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a user message."""
        if conversation_id not in self.active_conversations:
            print(f"Warning: Conversation {conversation_id} not found")
            return
        
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        conversation = self.active_conversations[conversation_id]
        conversation.messages.append(message)
        conversation.message_count += 1
        
        # Save message to database
        self._save_message_to_db(message)
    
    def log_assistant_message(self, conversation_id: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an assistant message."""
        if conversation_id not in self.active_conversations:
            print(f"Warning: Conversation {conversation_id} not found")
            return
        
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        conversation = self.active_conversations[conversation_id]
        conversation.messages.append(message)
        conversation.message_count += 1
        
        # Save message to database
        self._save_message_to_db(message)
    
    def end_conversation(self, conversation_id: str):
        """End a conversation."""
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]
            conversation.end_time = time.time()
            
            # Update database
            self._update_conversation_in_db(conversation)
            
            # Remove from active conversations
            del self.active_conversations[conversation_id]
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]
        
        # Try to load from database
        return self._load_conversation_from_db(conversation_id)
    
    def get_recent_conversations(self, limit: int = 10) -> List[Conversation]:
        """Get recent conversations."""
        try:
            conn = sqlite3.connect(self.conversation_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id FROM conversations 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            
            conversation_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            conversations = []
            for conv_id in conversation_ids:
                conv = self._load_conversation_from_db(conv_id)
                if conv:
                    conversations.append(conv)
            
            return conversations
            
        except Exception as e:
            print(f"Error loading recent conversations: {e}")
            return []
    
    def _save_conversation_to_db(self, conversation: Conversation):
        """Save conversation to database."""
        try:
            conn = sqlite3.connect(self.conversation_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO conversations 
                (id, model_id, start_time, end_time, message_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                conversation.id,
                conversation.model_id,
                conversation.start_time,
                conversation.end_time,
                conversation.message_count,
                json.dumps(conversation.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving conversation to database: {e}")
    
    def _save_message_to_db(self, message: ConversationMessage):
        """Save message to database."""
        try:
            conn = sqlite3.connect(self.conversation_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO messages 
                (id, conversation_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message.id,
                message.conversation_id,
                message.role,
                message.content,
                message.timestamp,
                json.dumps(message.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving message to database: {e}")
    
    def _update_conversation_in_db(self, conversation: Conversation):
        """Update conversation in database."""
        try:
            conn = sqlite3.connect(self.conversation_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE conversations 
                SET end_time = ?, message_count = ?, metadata = ?
                WHERE id = ?
            """, (
                conversation.end_time,
                conversation.message_count,
                json.dumps(conversation.metadata),
                conversation.id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error updating conversation in database: {e}")
    
    def _load_conversation_from_db(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from database."""
        try:
            conn = sqlite3.connect(self.conversation_db_path)
            cursor = conn.cursor()
            
            # Load conversation
            cursor.execute("""
                SELECT id, model_id, start_time, end_time, message_count, metadata
                FROM conversations WHERE id = ?
            """, (conversation_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            conv_id, model_id, start_time, end_time, message_count, metadata_json = row
            metadata = json.loads(metadata_json) if metadata_json else {}
            
            # Load messages
            cursor.execute("""
                SELECT id, role, content, timestamp, metadata
                FROM messages 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC
            """, (conversation_id,))
            
            messages = []
            for msg_row in cursor.fetchall():
                msg_id, role, content, timestamp, msg_metadata_json = msg_row
                msg_metadata = json.loads(msg_metadata_json) if msg_metadata_json else {}
                
                message = ConversationMessage(
                    id=msg_id,
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    timestamp=timestamp,
                    metadata=msg_metadata
                )
                messages.append(message)
            
            conn.close()
            
            conversation = Conversation(
                id=conv_id,
                model_id=model_id,
                start_time=start_time,
                end_time=end_time,
                message_count=message_count,
                messages=messages,
                metadata=metadata
            )
            
            return conversation
            
        except Exception as e:
            print(f"Error loading conversation from database: {e}")
            return None
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        try:
            conn = sqlite3.connect(self.conversation_db_path)
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute("SELECT COUNT(*) FROM conversations")
            total_conversations = cursor.fetchone()[0]
            
            # Total messages
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            # Recent activity (last 24 hours)
            twenty_four_hours_ago = time.time() - (24 * 60 * 60)
            cursor.execute("SELECT COUNT(*) FROM conversations WHERE start_time > ?", (twenty_four_hours_ago,))
            recent_conversations = cursor.fetchone()[0]
            
            # Active conversations
            active_count = len(self.active_conversations)
            
            conn.close()
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "recent_conversations_24h": recent_conversations,
                "active_conversations": active_count,
                "conversation_db_path": str(self.conversation_db_path)
            }
            
        except Exception as e:
            print(f"Error getting conversation stats: {e}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "recent_conversations_24h": 0,
                "active_conversations": len(self.active_conversations),
                "error": str(e)
            }


# Global conversation logger instance
conversation_logger = ConversationLogger()