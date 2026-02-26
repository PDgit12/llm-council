import unittest
import sys
import os
import time
from unittest.mock import MagicMock, patch

# Mock dependencies before importing storage
mock_firebase_admin = MagicMock()
mock_credentials = MagicMock()
mock_firestore = MagicMock()
mock_google_cloud = MagicMock()

sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock_credentials
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["google.cloud"] = mock_google_cloud
sys.modules["google.cloud.firestore"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import storage

class MockDocumentSnapshot:
    def __init__(self, data, doc_id):
        self._data = data
        self.id = doc_id
        self.reference = MagicMock()
        self.exists = True
        self._full_data = data

    def to_dict(self):
        return self._data

class StorageBenchmark(unittest.TestCase):
    def setUp(self):
        storage.db = MagicMock()
        self.mock_db = storage.db
        self.num_docs = 50
        self.message_count_per_doc = 20
        self.message_size = 500  # bytes

        # Full data dictionary for a document
        self.full_data_template = {
            "id": "doc_id",
            "created_at": "2023-01-01T00:00:00",
            "title": "Conversation",
            "messages": [{"role": "user", "content": "x" * self.message_size} for _ in range(self.message_count_per_doc)],
            "test_cases": [] # Assume small
        }

    def create_mock_docs(self, use_projection=False, has_message_count=True):
        docs = []
        for i in range(self.num_docs):
            full_data = self.full_data_template.copy()
            full_data["id"] = f"doc_{i}"
            full_data["title"] = f"Conversation {i}"
            full_data["created_at"] = f"2023-01-{i%28+1:02d}T00:00:00"

            if has_message_count:
                full_data["message_count"] = self.message_count_per_doc

            # If using projection, the initial snapshot only has selected fields
            if use_projection:
                projected_data = {
                    "id": full_data["id"],
                    "created_at": full_data["created_at"],
                    "title": full_data["title"],
                }
                if has_message_count:
                    projected_data["message_count"] = full_data["message_count"]

                doc = MockDocumentSnapshot(projected_data, full_data["id"])
                # The reference.get() should return the FULL data
                full_doc_snapshot = MockDocumentSnapshot(full_data, full_data["id"])
                doc.reference.get.return_value = full_doc_snapshot
            else:
                doc = MockDocumentSnapshot(full_data, full_data["id"])
                doc.reference.get.return_value = doc

            docs.append(doc)
        return docs

    def test_list_conversations_optimized(self):
        """
        Scenario: Data has 'message_count'. Code uses .select(), .order_by(), .limit(), .offset().
        Expectation: Fast, low bandwidth (simulated).
        """
        print("\n--- Benchmarking Optimized Scenario (New Data) ---")

        mock_docs = self.create_mock_docs(use_projection=True, has_message_count=True)

        # Mock chaining: db.collection().select().order_by().offset().limit().stream()
        mock_collection = self.mock_db.collection.return_value
        mock_select = mock_collection.select.return_value
        mock_order_by = mock_select.order_by.return_value
        mock_offset = mock_order_by.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.stream.return_value = iter(mock_docs)

        start_time = time.time()
        conversations = storage.list_conversations(limit=20, offset=10)
        end_time = time.time()

        # Verify chaining
        self.mock_db.collection.assert_called_with(storage.CONVERSATIONS_COLLECTION)
        mock_collection.select.assert_called_with(["id", "created_at", "title", "message_count"])
        mock_select.order_by.assert_called()
        mock_order_by.offset.assert_called_with(10)
        mock_offset.limit.assert_called_with(20)

        # Calculate simulated bandwidth
        total_size = sum(len(str(d._data)) for d in mock_docs)

        print(f"Time taken: {end_time - start_time:.6f}s")
        print(f"Total conversations: {len(conversations)}")
        print(f"Simulated Data Transferred: {total_size / 1024:.2f} KB")

        self.assertEqual(len(conversations), self.num_docs)
        self.assertEqual(conversations[0]['message_count'], self.message_count_per_doc)

        # Verify we didn't fetch full docs (reference.get() not called)
        for d in mock_docs:
            d.reference.get.assert_not_called()

    def test_list_conversations_legacy_fallback(self):
        """
        Scenario: Data missing 'message_count'. Code uses .select().
        Expectation: Fallback triggers full fetch.
        """
        print("\n--- Benchmarking Legacy Scenario (Fallback) ---")

        mock_docs = self.create_mock_docs(use_projection=True, has_message_count=False)

        # Mock chaining
        mock_collection = self.mock_db.collection.return_value
        mock_select = mock_collection.select.return_value
        mock_order_by = mock_select.order_by.return_value
        mock_offset = mock_order_by.offset.return_value
        mock_limit = mock_offset.limit.return_value
        mock_limit.stream.return_value = iter(mock_docs)

        start_time = time.time()
        conversations = storage.list_conversations()
        end_time = time.time()

        # Verify select was called
        mock_collection.select.assert_called()

        # Calculate simulated bandwidth
        initial_size = sum(len(str(d._data)) for d in mock_docs)
        fallback_size = 0
        for d in mock_docs:
            d.reference.get.assert_called()
            full_snapshot = d.reference.get.return_value
            fallback_size += len(str(full_snapshot._data))

        total_size = initial_size + fallback_size

        print(f"Time taken: {end_time - start_time:.6f}s")
        print(f"Total conversations: {len(conversations)}")
        print(f"Simulated Data Transferred: {total_size / 1024:.2f} KB")

        self.assertEqual(len(conversations), self.num_docs)
        self.assertEqual(conversations[0]['message_count'], self.message_count_per_doc)

if __name__ == '__main__':
    unittest.main()
