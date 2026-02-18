"""Firebase Firestore storage for conversations."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_SERVICE_ACCOUNT, FIREBASE_PROJECT_ID

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
            firebase_admin.initialize_app()
        
        db = firestore.client()
        print("Firebase initialized successfully.")
        return db
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        return None

# Always try to init on import
init_firebase()


def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """Create a new conversation in Firestore."""
    if db is None:
        raise RuntimeError("Firebase not initialized")

    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Task",
        "messages": [],
        "message_count": 0,
        "test_cases": []
    }

    db.collection("conversations").document(conversation_id).set(conversation)
    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Load a conversation from Firestore."""
    if db is None:
        return None

    doc = db.collection("conversations").document(conversation_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def save_conversation(conversation: Dict[str, Any]):
    """Save a conversation to Firestore."""
    if db is None:
        return

    db.collection("conversations").document(conversation['id']).update(conversation)


def list_conversations() -> List[Dict[str, Any]]:
    """List all conversations from Firestore (metadata only)."""
    if db is None:
        return []

    conversations = []
    # Fetch metadata only to optimize bandwidth
    # Ideally we'd also use pagination if there are many
    docs = db.collection("conversations").select(
        ["id", "created_at", "title", "message_count"]
    ).stream()
    
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
        "content": content
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
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any]
):
    """Add an assistant message with all 3 stages."""
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

    conversation["message_count"] = len(conversation["messages"])
    save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """Update the title of a conversation."""
    if db is None:
        return

    db.collection("conversations").document(conversation_id).update({"title": title})


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
    """Delete a conversation from Firestore."""
    if db is None:
        return False

    db.collection("conversations").document(conversation_id).delete()
    return True
