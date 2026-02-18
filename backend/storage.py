"""Storage backend for Parallels (Firebase + Local JSON Fallback)."""

import json
import os
import glob
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_SERVICE_ACCOUNT, FIREBASE_PROJECT_ID, DATA_DIR

CONVERSATIONS_COLLECTION = "conversations"

# Initialize Firebase
db = None

def init_firebase():
    """Initialize Firebase Admin SDK."""
    global db
    if db is not None:
        return db

    try:
        if FIREBASE_SERVICE_ACCOUNT:
            if os.path.exists(FIREBASE_SERVICE_ACCOUNT):
                cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
            else:
                # Assume it's stringified JSON
                cred_json = json.loads(FIREBASE_SERVICE_ACCOUNT)
                cred = credentials.Certificate(cred_json)
            
            firebase_admin.initialize_app(cred, {
                'projectId': FIREBASE_PROJECT_ID
            })
        else:
            # Try default credentials (ADC)
            # Only try if we think we might be in an environment with ADC (e.g. Google Cloud)
            # or explicitly requested. For now, we'll skip if no explicitly provided creds
            # to default to local storage easily.
            # firebase_admin.initialize_app()
            pass
        
        if firebase_admin._apps:
            db = firestore.client()
            print("Firebase initialized successfully.")
            return db
    except Exception as e:
        print(f"Firebase initialization skipped/failed: {e}")
        return None

# Always try to init on import, but don't fail if it doesn't work
init_firebase()

# Ensure local data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def _get_local_path(conversation_id: str) -> str:
    return os.path.join(DATA_DIR, f"{conversation_id}.json")

def _load_local(conversation_id: str) -> Optional[Dict[str, Any]]:
    path = _get_local_path(conversation_id)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading local conversation {conversation_id}: {e}")
    return None

def _save_local(conversation: Dict[str, Any]):
    path = _get_local_path(conversation['id'])
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)

def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """Create a new conversation."""
    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Task",
        "messages": [],
        "message_count": 0,
        "test_cases": []
    }

    db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).set(conversation)
    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Load a conversation."""
    if db:
        doc = db.collection("conversations").document(conversation_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    doc = db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def save_conversation(conversation: Dict[str, Any]):
    """Save a conversation to Firestore."""
    if db is None:
        return

    db.collection(CONVERSATIONS_COLLECTION).document(conversation['id']).update(conversation)


def list_conversations() -> List[Dict[str, Any]]:
    """List all conversations (metadata only)."""
    conversations = []
    # Fetch all docs, but ideally we'd use pagination if there are many
    docs = db.collection(CONVERSATIONS_COLLECTION).stream()
    
    for doc in docs:
        data = doc.to_dict()
        message_count = data.get("message_count")

        # Fallback for legacy documents without 'message_count'
        if message_count is None:
            # We must fetch the full doc (or at least messages) to count them.
            # Using reference.get() fetches the full document.
            try:
                full_doc = doc.reference.get()
                if full_doc.exists:
                    full_data = full_doc.to_dict()
                    message_count = len(full_data.get("messages", []))
                else:
                    message_count = 0
            except Exception as e:
                print(f"Error fetching legacy doc {doc.id}: {e}")
                message_count = 0

        conversations.append({
            "id": data["id"],
            "created_at": data["created_at"],
            "title": data.get("title", "New Task"),
            "message_count": message_count
        })

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)
    return conversations


def count_conversations() -> int:
    """Count all conversations in Firestore."""
    if db is None:
        return 0

    try:
        # Use aggregation query for efficiency
        query = db.collection("conversations")
        count_query = query.count()
        snapshot = count_query.get()

        # Handle different return types from SDK versions
        if isinstance(snapshot, list) and len(snapshot) > 0:
            first = snapshot[0]
            if isinstance(first, list) and len(first) > 0:
                return int(first[0].value)
            elif hasattr(first, 'value'):
                return int(first.value)

        # Fallback for unexpected structure
        print(f"Unexpected aggregation result structure: {snapshot}")
        return len(list_conversations())

    except Exception as e:
        print(f"Error counting conversations: {e}")
        # Fallback to inefficient method
        return len(list_conversations())


def add_user_message(
    conversation_id: str, 
    content: str, 
    attachments: Optional[List[Dict[str, Any]]] = None
):
    """Add a user message to a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    message = {
        "role": "user",
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if attachments:
        message["attachments"] = attachments

    if "messages" not in conversation:
        conversation["messages"] = []
        
    conversation["messages"].append(message)
    conversation["message_count"] = len(conversation["messages"])
    save_conversation(conversation)


def add_assistant_message(
    conversation_id: str,
    result: Dict[str, Any]
):
    """Add an assistant message with the full pipeline result."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    if "messages" not in conversation:
        conversation["messages"] = []

    message = {
        "role": "assistant"
    }
    # Merge all result fields (stage1, stage2, final_answer, etc.)
    message.update(result)

    # Ensure standard 'content' field is present for compatibility
    if "content" not in message and "final_answer" in message:
        message["content"] = message["final_answer"]

    conversation["messages"].append(message)
    save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """Update the title of a conversation."""
    if db is None:
        return

    db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).update({"title": title})


def add_test_case(conversation_id: str, input_data: str, expected_output: str) -> Dict[str, Any]:
    """Add a test case to a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")
    
    test_case = {
        "id": str(datetime.now().timestamp()).replace('.', ''),
        "input": input_data,
        "expected": expected_output
    }
    
    if "test_cases" not in conversation:
        conversation["test_cases"] = []
    
    conversation["test_cases"].append(test_case)
    save_conversation(conversation)
    return test_case


def delete_test_case(conversation_id: str, test_case_id: str) -> bool:
    """Delete a test case from a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        return False
    
    if "test_cases" not in conversation:
        return False
    
    initial_len = len(conversation["test_cases"])
    conversation["test_cases"] = [tc for tc in conversation["test_cases"] if tc["id"] != test_case_id]
    
    if len(conversation["test_cases"]) < initial_len:
        save_conversation(conversation)
        return True
    return False


def get_test_cases(conversation_id: str) -> List[Dict[str, Any]]:
    """Get all test cases for a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        return []
    return conversation.get("test_cases", [])


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation."""
    if db:
        db.collection("conversations").document(conversation_id).delete()
        return True
    else:
        path = _get_local_path(conversation_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).delete()
    return True
