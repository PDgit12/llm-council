import sys
import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

# Mock firebase_admin and google.cloud before importing backend.storage
# This is necessary because backend.storage initializes firebase on import
mock_firebase_admin = MagicMock()
mock_credentials = MagicMock()
mock_firestore = MagicMock()
mock_google_cloud = MagicMock()

sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock_credentials
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["google.cloud"] = mock_google_cloud
sys.modules["google.cloud.firestore"] = MagicMock()

# Now import the module under test
from backend import storage

class TestStorage(unittest.TestCase):
    def setUp(self):
        # Reset the mock db before each test
        storage.db = MagicMock()
        self.mock_db = storage.db
        self.mock_collection = self.mock_db.collection.return_value
        self.mock_document = self.mock_collection.document.return_value

    def test_create_conversation_success(self):
        """Test creating a conversation successfully."""
        conversation_id = "test_conv_123"

        # Call the function
        result = storage.create_conversation(conversation_id)

        # Verify the structure of the returned dictionary
        self.assertEqual(result["id"], conversation_id)
        self.assertEqual(result["title"], "New Task")
        self.assertEqual(result["messages"], [])
        self.assertEqual(result["test_cases"], [])
        self.assertTrue("created_at" in result)

        # Verify Firestore interactions
        self.mock_db.collection.assert_called_once_with("conversations")
        self.mock_collection.document.assert_called_once_with(conversation_id)
        self.mock_document.set.assert_called_once_with(result)

    @patch('backend.storage._save_local')
    def test_create_conversation_db_not_initialized(self, mock_save_local):
        """Test create_conversation when db is None."""
        storage.db = None
        conversation_id = "test_conv_local"

        result = storage.create_conversation(conversation_id)

        self.assertEqual(result["id"], conversation_id)
        mock_save_local.assert_called_once_with(result)

    def test_get_conversation_exists(self):
        """Test getting an existing conversation."""
        conversation_id = "test_conv_123"
        expected_data = {
            "id": conversation_id,
            "title": "Existing Task",
            "messages": []
        }

        # Setup mock return value
        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.exists = True
        mock_doc_snapshot.to_dict.return_value = expected_data
        self.mock_document.get.return_value = mock_doc_snapshot

        # Call the function
        result = storage.get_conversation(conversation_id)

        # Verify
        self.assertEqual(result, expected_data)
        self.mock_db.collection.assert_called_once_with("conversations")
        self.mock_collection.document.assert_called_once_with(conversation_id)
        self.mock_document.get.assert_called_once()

    def test_get_conversation_not_exists(self):
        """Test getting a non-existent conversation."""
        conversation_id = "test_conv_404"

        # Setup mock return value
        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.exists = False
        self.mock_document.get.return_value = mock_doc_snapshot

        # Call the function
        result = storage.get_conversation(conversation_id)

        # Verify
        self.assertIsNone(result)

    @patch('backend.storage._load_local')
    def test_get_conversation_db_not_initialized(self, mock_load_local):
        """Test get_conversation when db is None."""
        storage.db = None
        conversation_id = "test_conv_local"
        expected_data = {"id": conversation_id, "title": "Local Task"}
        mock_load_local.return_value = expected_data

        result = storage.get_conversation(conversation_id)

        self.assertEqual(result, expected_data)
        mock_load_local.assert_called_once_with(conversation_id)

    def test_save_conversation(self):
        """Test saving a conversation."""
        conversation = {
            "id": "test_conv_123",
            "title": "Updated Title",
            "messages": [{"role": "user", "content": "Hi"}]
        }

        storage.save_conversation(conversation)

        self.mock_db.collection.assert_called_with("conversations")
        self.mock_collection.document.assert_called_with(conversation["id"])
        self.mock_document.update.assert_called_once_with(conversation)

    @patch('backend.storage._save_local')
    def test_save_conversation_db_not_initialized(self, mock_save_local):
        """Test saving a conversation when db is None."""
        storage.db = None
        conversation = {"id": "test_conv_local", "title": "Local"}

        storage.save_conversation(conversation)

        mock_save_local.assert_called_once_with(conversation)

    def test_list_conversations(self):
        """Test listing conversations."""
        # Setup mock stream
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {
            "id": "c1", "created_at": "2023-01-01", "title": "T1", "messages": [], "message_count": 0
        }
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {
            "id": "c2", "created_at": "2023-01-02", "title": "T2", "messages": [1, 2], "message_count": 2
        }
        self.mock_collection.stream.return_value = [mock_doc1, mock_doc2]

        result = storage.list_conversations()

        self.assertEqual(len(result), 2)
        # Verify sorting (newest first)
        self.assertEqual(result[0]["id"], "c2")
        self.assertEqual(result[1]["id"], "c1")

        self.assertEqual(result[0]["message_count"], 2)
        self.assertEqual(result[1]["message_count"], 0)

    @patch('os.listdir')
    @patch('backend.storage._load_local')
    def test_list_conversations_db_not_initialized(self, mock_load_local, mock_listdir):
        """Test listing conversations when db is None."""
        storage.db = None
        mock_listdir.return_value = ["c1.json", "c2.json", "other.txt"]
        mock_load_local.side_effect = [
            {"id": "c1", "created_at": "2023-01-01", "title": "T1", "messages": []},
            {"id": "c2", "created_at": "2023-01-02", "title": "T2", "messages": [1]}
        ]

        result = storage.list_conversations()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "c2") # Sorted by date
        self.assertEqual(result[1]["id"], "c1")

    @patch('backend.storage.get_conversation')
    @patch('backend.storage.save_conversation')
    def test_add_user_message(self, mock_save, mock_get):
        """Test adding a user message."""
        conversation_id = "test_c1"
        initial_conv = {"id": conversation_id, "messages": []}
        mock_get.return_value = initial_conv

        storage.add_user_message(conversation_id, "Hello")

        mock_get.assert_called_once_with(conversation_id)
        self.assertEqual(len(initial_conv["messages"]), 1)
        self.assertEqual(initial_conv["messages"][0]["role"], "user")
        self.assertEqual(initial_conv["messages"][0]["content"], "Hello")
        mock_save.assert_called_once_with(initial_conv)

    @patch('backend.storage.get_conversation')
    @patch('backend.storage.save_conversation')
    def test_add_assistant_message(self, mock_save, mock_get):
        """Test adding an assistant message."""
        conversation_id = "test_c1"
        initial_conv = {"id": conversation_id, "messages": []}
        mock_get.return_value = initial_conv

        result = {
            "stage1": [{"thought": "t1"}],
            "stage2": [{"thought": "t2"}],
            "final_answer": "answer"
        }

        storage.add_assistant_message(conversation_id, result)

        self.assertEqual(len(initial_conv["messages"]), 1)
        msg = initial_conv["messages"][0]
        self.assertEqual(msg["role"], "assistant")
        self.assertEqual(msg["stage1"], result["stage1"])
        self.assertEqual(msg["stage2"], result["stage2"])
        self.assertEqual(msg["final_answer"], result["final_answer"])
        self.assertEqual(msg["content"], result["final_answer"])

        mock_save.assert_called_once_with(initial_conv)

    def test_update_conversation_title(self):
        """Test updating conversation title."""
        conversation_id = "test_c1"
        new_title = "New Title"

        storage.update_conversation_title(conversation_id, new_title)

        self.mock_collection.document.assert_called_with(conversation_id)
        self.mock_document.update.assert_called_once_with({"title": new_title})

    @patch('backend.storage._load_local')
    @patch('backend.storage._save_local')
    def test_update_conversation_title_db_not_initialized(self, mock_save_local, mock_load_local):
        """Test updating title when db is None."""
        storage.db = None
        conversation_id = "test_conv_local"
        mock_load_local.return_value = {"id": conversation_id, "title": "Old"}

        storage.update_conversation_title(conversation_id, "New")

        mock_load_local.assert_called_once_with(conversation_id)
        mock_save_local.assert_called_once()
        saved_conv = mock_save_local.call_args[0][0]
        self.assertEqual(saved_conv["title"], "New")

    @patch('backend.storage.get_conversation')
    @patch('backend.storage.save_conversation')
    def test_add_test_case(self, mock_save, mock_get):
        """Test adding a test case."""
        conversation_id = "test_c1"
        initial_conv = {"id": conversation_id, "test_cases": []}
        mock_get.return_value = initial_conv

        result = storage.add_test_case(conversation_id, "input", "expected")

        self.assertEqual(len(initial_conv["test_cases"]), 1)
        self.assertEqual(initial_conv["test_cases"][0], result)
        self.assertEqual(result["input"], "input")
        self.assertEqual(result["expected"], "expected")

        mock_save.assert_called_once_with(initial_conv)

    @patch('backend.storage.get_conversation')
    @patch('backend.storage.save_conversation')
    def test_delete_test_case(self, mock_save, mock_get):
        """Test deleting a test case."""
        conversation_id = "test_c1"
        tc_id = "tc1"
        initial_conv = {
            "id": conversation_id,
            "test_cases": [{"id": tc_id, "input": "i", "expected": "e"}]
        }
        mock_get.return_value = initial_conv

        success = storage.delete_test_case(conversation_id, tc_id)

        self.assertTrue(success)
        self.assertEqual(len(initial_conv["test_cases"]), 0)
        mock_save.assert_called_once_with(initial_conv)

    def test_delete_conversation(self):
        """Test deleting a conversation."""
        conversation_id = "test_c1"

        success = storage.delete_conversation(conversation_id)

        self.assertTrue(success)
        self.mock_collection.document.assert_called_with(conversation_id)
        self.mock_document.delete.assert_called_once()

    @patch('os.path.exists')
    @patch('os.remove')
    def test_delete_conversation_db_not_initialized(self, mock_remove, mock_exists):
        """Test deleting conversation when db is None."""
        storage.db = None
        conversation_id = "test_conv_local"
        mock_exists.return_value = True

        success = storage.delete_conversation(conversation_id)

        self.assertTrue(success)
        mock_remove.assert_called_once()

if __name__ == "__main__":
    unittest.main()
