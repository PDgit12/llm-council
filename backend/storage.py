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
        "test_cases": []
    }

    if db:
        db.collection("conversations").document(conversation_id).set(conversation)
    else:
        _save_local(conversation)

    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Load a conversation."""
    if db:
        doc = db.collection("conversations").document(conversation_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    else:
        return _load_local(conversation_id)


def save_conversation(conversation: Dict[str, Any]):
    """Save a conversation."""
    if db:
        db.collection("conversations").document(conversation['id']).update(conversation)
    else:
        _save_local(conversation)


def list_conversations() -> List[Dict[str, Any]]:
    """List all conversations (metadata only)."""
    conversations = []
    
    if db:
        # Fetch all docs, but ideally we'd use pagination if there are many
        docs = db.collection("conversations").stream()
        for doc in docs:
            data = doc.to_dict()
            conversations.append({
                "id": data["id"],
                "created_at": data["created_at"],
                "title": data.get("title", "New Task"),
                "message_count": len(data.get("messages", []))
            })
    else:
        # Local storage
        files = glob.glob(os.path.join(DATA_DIR, "*.json"))
        for path in files:
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    conversations.append({
                        "id": data["id"],
                        "created_at": data["created_at"],
                        "title": data.get("title", "New Task"),
                        "message_count": len(data.get("messages", []))
                    })
            except Exception as e:
                print(f"Error reading {path}: {e}")

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)
    return conversations


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
    save_conversation(conversation)


def add_assistant_message(
    conversation_id: str,
    stage1: Optional[List[Dict[str, Any]]] = None,
    stage2: Optional[List[Dict[str, Any]]] = None,
    stage3: Optional[Union[Dict[str, Any], str]] = None, # Can be passed as final string by legacy code
    final_answer: Optional[str] = None
):
    """Add an assistant message with all stages."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    if "messages" not in conversation:
        conversation["messages"] = []

    # Handle argument flexibility
    actual_stage3 = {}
    actual_final_answer = final_answer

    if isinstance(stage3, str):
        actual_final_answer = stage3
    elif isinstance(stage3, dict):
        actual_stage3 = stage3

    # If final_answer wasn't provided but logic implies it should exist
    if actual_final_answer is None and isinstance(stage3, str):
         actual_final_answer = stage3

    conversation["messages"].append({
        "role": "assistant",
        "stage1": stage1 or [],
        "stage2": stage2 or [],
        "stage3": actual_stage3,
        "final_answer": actual_final_answer or "",
        "timestamp": datetime.utcnow().isoformat()
    })

    save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """Update the title of a conversation."""
    if db:
        db.collection("conversations").document(conversation_id).update({"title": title})
    else:
        conversation = _load_local(conversation_id)
        if conversation:
            conversation["title"] = title
            _save_local(conversation)


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
