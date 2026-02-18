import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add backend directory to sys.path so that 'import config' works inside storage.py
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock firebase_admin before importing storage to avoid initialization error
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.firestore'] = MagicMock()

import storage
import main
from main import CreateConversationRequest

class TestConversationCount(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_db = MagicMock()

        # Patch the db used by storage.py (which is used by main.py)
        storage.db = self.mock_db

        self.mock_collection = self.mock_db.collection.return_value
        self.mock_count_query = self.mock_collection.count.return_value
        # Mock count return value (below limit)
        mock_agg_result = MagicMock()
        mock_agg_result.value = 5
        # Return list of list of result
        self.mock_count_query.get.return_value = [[mock_agg_result]]

    async def test_create_conversation_uses_count(self):
        # Mock request
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_body = CreateConversationRequest()

        # Mock rate limit
        with patch('main.check_rate_limit'):
            # Mock storage.create_conversation to prevent actual DB call
            with patch.object(storage, 'create_conversation') as mock_create:
                mock_create.return_value = {"id": "new-id", "messages": []}

                # Run
                await main.create_conversation(mock_request, mock_body)

                # Verify count() was called
                self.mock_collection.count.assert_called_once()

                # Verify stream() was NOT called
                self.mock_collection.stream.assert_not_called()

if __name__ == '__main__':
    unittest.main()
