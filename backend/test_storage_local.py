import unittest
import os
import json
import shutil
import uuid
from datetime import datetime
from config import DATA_DIR
import storage

# Force disable Firebase for this test by mocking or ensuring no creds?
# storage.db is None if init failed.
# We'll assume storage.db is None for this test since we are in a sandbox without firebase creds.
# If it is not None, we force it to None.
storage.db = None

class TestLocalStorage(unittest.TestCase):
    def setUp(self):
        # Create a temporary test directory if needed, or just use the data dir
        # We will use the actual DATA_DIR but clean up our test files
        self.test_id = f"test_{uuid.uuid4()}"

    def tearDown(self):
        # Clean up
        storage.delete_conversation(self.test_id)

    def test_crud_conversation(self):
        # Create
        conv = storage.create_conversation(self.test_id)
        self.assertEqual(conv['id'], self.test_id)
        self.assertTrue(os.path.exists(os.path.join(DATA_DIR, f"{self.test_id}.json")))

        # Get
        loaded = storage.get_conversation(self.test_id)
        self.assertEqual(loaded['id'], self.test_id)

        # List
        all_convs = storage.list_conversations()
        ids = [c['id'] for c in all_convs]
        self.assertIn(self.test_id, ids)

        # Update Title
        storage.update_conversation_title(self.test_id, "Updated Title")
        loaded = storage.get_conversation(self.test_id)
        self.assertEqual(loaded['title'], "Updated Title")

        # Delete
        storage.delete_conversation(self.test_id)
        self.assertFalse(os.path.exists(os.path.join(DATA_DIR, f"{self.test_id}.json")))
        loaded = storage.get_conversation(self.test_id)
        self.assertIsNone(loaded)

    def test_messages(self):
        storage.create_conversation(self.test_id)

        # Add User Message
        storage.add_user_message(self.test_id, "Hello World")
        conv = storage.get_conversation(self.test_id)
        self.assertEqual(len(conv['messages']), 1)
        self.assertEqual(conv['messages'][0]['role'], 'user')
        self.assertEqual(conv['messages'][0]['content'], "Hello World")

        # Add Assistant Message (flexible)
        storage.add_assistant_message(
            self.test_id,
            stage1=[{"content": "s1"}],
            final_answer="Final Answer"
        )
        conv = storage.get_conversation(self.test_id)
        self.assertEqual(len(conv['messages']), 2)
        self.assertEqual(conv['messages'][1]['role'], 'assistant')
        self.assertEqual(conv['messages'][1]['final_answer'], "Final Answer")
        self.assertEqual(conv['messages'][1]['stage1'][0]['content'], "s1")

if __name__ == '__main__':
    unittest.main()
