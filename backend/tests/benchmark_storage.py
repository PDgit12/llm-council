import unittest
import sys
import os
import time
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import storage

class MockDocumentSnapshot:
    def __init__(self, data, doc_id):
        self._data = data
        self.id = doc_id
        self.reference = MagicMock()
        self.exists = True

        # Simulate .get() on reference returning a FULL document snapshot
        # For legacy test, this will be used to fetch the full doc.
        # We need to ensure that when .get() is called, it returns a snapshot with the FULL data.
        # But wait, self._data might be the projected data (missing fields).
        # So we need a way to store the full data separately if this is a projected snapshot.
        self._full_data = data

    def to_dict(self):
        return self._data

class StorageBenchmark(unittest.TestCase):
    def setUp(self):
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

    @patch('storage.db')
    def test_list_conversations_optimized(self, mock_db):
        """
        Scenario: Data has 'message_count'. Code uses .select().
        Expectation: Fast, low bandwidth (simulated).
        """
        print("\n--- Benchmarking Optimized Scenario (New Data) ---")

        mock_docs = self.create_mock_docs(use_projection=True, has_message_count=True)

        # Mock .select().stream()
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        mock_query = MagicMock()
        mock_collection.select.return_value = mock_query
        mock_query.stream.return_value = iter(mock_docs)

        start_time = time.time()
        conversations = storage.list_conversations()
        end_time = time.time()

        # Verify select was called with correct fields
        mock_collection.select.assert_called_with(["id", "created_at", "title", "message_count"])

        # Calculate simulated bandwidth
        # We fetched the projected docs.
        total_size = sum(len(str(d._data)) for d in mock_docs)

        print(f"Time taken: {end_time - start_time:.6f}s")
        print(f"Total conversations: {len(conversations)}")
        print(f"Simulated Data Transferred: {total_size / 1024:.2f} KB")

        self.assertEqual(len(conversations), self.num_docs)
        self.assertEqual(conversations[0]['message_count'], self.message_count_per_doc)

        # Verify we didn't fetch full docs (reference.get() not called)
        for d in mock_docs:
            d.reference.get.assert_not_called()

    @patch('storage.db')
    def test_list_conversations_legacy_fallback(self, mock_db):
        """
        Scenario: Data missing 'message_count'. Code uses .select().
        Expectation: Fallback triggers full fetch. High bandwidth/Slow.
        """
        print("\n--- Benchmarking Legacy Scenario (Fallback) ---")

        mock_docs = self.create_mock_docs(use_projection=True, has_message_count=False)

        # Mock .select().stream()
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        mock_query = MagicMock()
        mock_collection.select.return_value = mock_query
        mock_query.stream.return_value = iter(mock_docs)

        start_time = time.time()
        conversations = storage.list_conversations()
        end_time = time.time()

        # Verify select was called
        mock_collection.select.assert_called()

        # Calculate simulated bandwidth
        # 1. Initial projected fetch
        initial_size = sum(len(str(d._data)) for d in mock_docs)

        # 2. Fallback full fetch for each doc
        # Each doc had .reference.get() called, returning full doc
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
    storage.db = MagicMock()
    unittest.main()
