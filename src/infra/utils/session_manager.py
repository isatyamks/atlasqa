import logging

logger = logging.getLogger(__name__)

from datetime import timezone
from typing import Dict, List, Optional

import pymongo


class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.sessions: Dict[str, deque] = {}
            cls._instance.max_history = 10  # Keep last 10 turns
            cls._instance.session_expiry = (
                3600  # 1 hour expiry (not implemented yet, but good practice)
            )

            try:
                cls._instance.mongo_client = pymongo.MongoClient(
                    settings.MONGO_URI, serverSelectionTimeoutMS=2000
                )
                cls._instance.db = cls._instance.mongo_client[settings.MONGO_DB_NAME]
                cls._instance.collection = cls._instance.db["sessions"]
            except Exception as e:
                print(f"Error connecting to MongoDB: {e}")
                cls._instance.collection = None

        return cls._instance

    def _load_session(self, session_id: str) -> bool:
        """Attempts to load a session from mongo_db. Returns True if successful."""
        if self.collection is None:
            return False

        try:
            doc = self.collection.find_one({"_id": session_id})
            if doc and "history" in doc:
                self.sessions[session_id] = deque(
                    doc["history"], maxlen=self.max_history
                )
                return True
        except Exception as e:
            print(f"Error loading session {session_id} from mongo_db: {e}")
        return False

    def _save_session(self, session_id: str):
        """Saves a session to MongoDB."""
        if session_id in self.sessions and self.collection is not None:
            try:
                now = datetime.now(timezone.utc)
                self.collection.update_one(
                    {"_id": session_id},
                    {
                        "$set": {
                            "history": list(self.sessions[session_id]),
                            "updated_at": now,
                        },
                        "$setOnInsert": {"created_at": now},
                    },
                    upsert=True,
                )
            except Exception as e:
                print(f"Error saving session {session_id} to MongoDB: {e}")

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        if session_id not in self.sessions:
            if not self._load_session(session_id):
                return []
        return list(self.sessions[session_id])

    def get_all_sessions(self) -> List[Dict]:
        """Fetch all sessions to act as projects in the frontend"""
        if self.collection is None:
            return []
        try:
            docs = self.collection.find(
                {}, {"_id": 1, "created_at": 1, "updated_at": 1, "history": 1}
            )
            return list(docs)
        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []

    def add_turn(
        self,
        session_id: str,
        user_query: str,
        ai_response: str,
        raw_json: Optional[Dict] = None,
    ):
        if session_id not in self.sessions:
            if not self._load_session(session_id):
                self.sessions[session_id] = deque(maxlen=self.max_history)

        now = datetime.now(timezone.utc).isoformat()
        self.sessions[session_id].append(
            {"role": "user", "content": user_query, "timestamp": now}
        )

        assistant_turn = {"role": "assistant", "content": ai_response, "timestamp": now}
        if raw_json is not None:
            assistant_turn["raw_json"] = raw_json

        self.sessions[session_id].append(assistant_turn)
        self._save_session(session_id)

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

        if self.collection is not None:
            try:
                self.collection.delete_one({"_id": session_id})
            except Exception as e:
                print(f"Error deleting session {session_id} from mongo_db: {e}")

    def format_history_for_llm(self, session_id: str) -> str:
        """Formats history as a string for LLM prompts"""
        history = self.get_history(session_id)
        if not history:
            return ""

        formatted = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")

        return "\n".join(formatted)
