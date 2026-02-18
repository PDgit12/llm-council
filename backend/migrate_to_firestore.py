"""One-time migration script from local JSON to Firestore."""

import os
import json
import storage
from config import DATA_DIR

def migrate():
    """Read all local JSON files and upload to Firestore."""
    print(f"Starting migration from {DATA_DIR}...")
    
    # Ensure Firebase is initialized
    db = storage.init_firebase()
    if db is None:
        print("Error: Could not initialize Firebase. Check your credentials.")
        return

    if not os.path.exists(DATA_DIR):
        print(f"Directory {DATA_DIR} does not exist. Nothing to migrate.")
        return

    count = 0
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(DATA_DIR, filename)
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                # Add message_count for optimized listing
                if "messages" in data:
                    data["message_count"] = len(data["messages"])
                else:
                    data["message_count"] = 0

                # Use storage methods to save to Firestore
                print(f"Migrating {data['id']} ({data.get('title', 'Untitled')})...")
                
                # Check if it already exists to avoid duplicates (optional)
                doc_ref = db.collection(storage.CONVERSATIONS_COLLECTION).document(data['id'])
                if doc_ref.get().exists:
                    print(f"  - Document {data['id']} already exists in Firestore. Overwriting.")
                
                doc_ref.set(data)
                count += 1
            except Exception as e:
                print(f"  - Failed to migrate {filename}: {e}")

    print(f"Migration complete! Total documents migrated: {count}")

if __name__ == "__main__":
    migrate()
