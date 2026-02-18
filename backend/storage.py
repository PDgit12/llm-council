import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_SERVICE_ACCOUNT, FIREBASE_PROJECT_ID

# Initialize Firebase
db = None

# Local Storage (In-Memory for now, or file-based)
LOCAL_STORAGE_FILE = "local_db.json"
local_db = {}

def load_local_db():
    global local_db
    if os.path.exists(LOCAL_STORAGE_FILE):
        try:
            with open(LOCAL_STORAGE_FILE, 'r') as f:
                local_db = json.load(f)
        except json.JSONDecodeError:
            local_db = {}
    else:
        local_db = {}

def save_local_db():
    global local_db
    with open(LOCAL_STORAGE_FILE, 'w') as f:
        json.dump(local_db, f, indent=2)

def init_firebase():
    """Initialize Firebase Admin SDK or fallback to local storage."""
    global db

    # Check for local storage override
    if os.environ.get("USE_LOCAL_STORAGE", "false").lower() == "true":
        print("Using LOCAL STORAGE (simulated database).")
        load_local_db()
        return None

    if db is not None:
        return db

    try:
        # [Existing Firebase Init Logic]
        if FIREBASE_SERVICE_ACCOUNT:
            if os.path.exists(FIREBASE_SERVICE_ACCOUNT):
                cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
            else:
                cred_json = json.loads(FIREBASE_SERVICE_ACCOUNT)
                cred = credentials.Certificate(cred_json)
            
            firebase_admin.initialize_app(cred, {
                'projectId': FIREBASE_PROJECT_ID
            })
        else:
             # Try default credentials (ADC)
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app()
        
        db = firestore.client()
        print("Firebase initialized successfully.")
        return db
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        print("Falling back to LOCAL STORAGE.")
        load_local_db()
        return None

# Always try to init on import
init_firebase()


def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """Create a new conversation in Firestore or Local Storage."""
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
        local_db[conversation_id] = conversation
        save_local_db()

    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Load a conversation."""
    if db:
        doc = db.collection("conversations").document(conversation_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    else:
        return local_db.get(conversation_id)


def save_conversation(conversation: Dict[str, Any]):
    """Save a conversation."""
    if db:
        db.collection("conversations").document(conversation['id']).update(conversation)
    else:
        local_db[conversation['id']] = conversation
        save_local_db()


def list_conversations() -> List[Dict[str, Any]]:
    """List all conversations."""
    conversations = []
    
    if db:
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
        for cid, data in local_db.items():
            conversations.append({
                "id": data["id"],
                "created_at": data["created_at"],
                "title": data.get("title", "New Task"),
                "message_count": len(data.get("messages", []))
            })

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)
    return conversations

def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation."""
    if db:
        db.collection("conversations").document(conversation_id).delete()
    else:
        if conversation_id in local_db:
            del local_db[conversation_id]
            save_local_db()
            return True
        return False

# ... [The rest of the helper functions for messages/tests can remain mostly as is,
# relying on get_conversation and save_conversation which are now abstracted] ...

def add_user_message(
    conversation_id: str, 
    content: str, 
    attachments: Optional[List[Dict[str, Any]]] = None
):
    """Add a user message to a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    if "messages" not in conversation:
        conversation["messages"] = []

    message = {
        "role": "user",
        "content": content
    }
    
    if attachments:
        message["attachments"] = attachments
        
    conversation["messages"].append(message)
    save_conversation(conversation)


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any]
):
    # This function signature is slightly legacy compared to the new stream
    # but still valid for the non-stream endpoints if used.
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    if "messages" not in conversation:
        conversation["messages"] = []

    conversation["messages"].append({
        "role": "assistant",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3
    })

    save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """Update the title of a conversation."""
    if db:
        db.collection("conversations").document(conversation_id).update({"title": title})
    else:
        if conversation_id in local_db:
            local_db[conversation_id]["title"] = title
            save_local_db()


def add_test_case(conversation_id: str, input_data: str, expected_output: str) -> Dict[str, Any]:
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
    conversation = get_conversation(conversation_id)
    if conversation is None:
        return []
    return conversation.get("test_cases", [])
