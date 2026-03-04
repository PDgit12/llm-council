import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add root to path
sys.path.append(os.getcwd())

# Mock all external dependencies to verify logic in isolation
sys.modules['httpx'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Mock PIL and PIL.Image
mock_pil = MagicMock()
sys.modules['PIL'] = mock_pil
mock_pil_image = MagicMock()
sys.modules['PIL.Image'] = mock_pil_image
mock_pil.Image = mock_pil_image

# Mock config
sys.modules['config'] = MagicMock()

try:
    from backend.openrouter import _load_local_image
except ImportError as e:
    print(f"Failed to import backend.openrouter: {e}")
    sys.exit(1)

class TestRefactoredImageHelper(unittest.TestCase):
    @patch('backend.openrouter.os.path.exists')
    @patch('backend.openrouter.PIL.Image.open')
    def test_load_local_image(self, mock_open, mock_exists):
        # Configure mocks
        mock_exists.return_value = True
        mock_image_obj = MagicMock()
        mock_open.return_value = mock_image_obj

        # Test cases
        cases = [
            ('/uploads/image.png', os.path.join('data', 'uploads/image.png')),
            ('uploads/image.png', os.path.join('data', 'uploads/image.png')),
            ('data/uploads/image.png', 'data/uploads/image.png'),
            ('/data/uploads/image.png', 'data/uploads/image.png'),
            ('image.png', os.path.join('data/uploads', 'image.png')),
            ('/image.png', os.path.join('data/uploads', 'image.png')),
        ]

        for input_path, expected_path in cases:
            # Update expectation to absolute path due to security fix
            expected_path = os.path.abspath(expected_path)

            with self.subTest(path=input_path):
                # Reset mocks
                mock_exists.reset_mock()
                mock_open.reset_mock()
                mock_exists.return_value = True
                mock_open.return_value = mock_image_obj

                result = _load_local_image(input_path)

                mock_exists.assert_called_with(expected_path)
                mock_open.assert_called_with(expected_path)
                self.assertEqual(result, mock_image_obj)

    @patch('backend.openrouter.os.path.exists')
    def test_path_traversal_prevention(self, mock_exists):
        """Test that path traversal attempts are blocked."""
        # Even if file exists, it should be blocked
        mock_exists.return_value = True

        # Attack vectors
        # Note: These paths attempt to go outside the 'data' directory
        # The exact resolution depends on where the test runs, but '..' should trigger checks
        vectors = [
            'uploads/../../secret.txt',
            'data/../secret.txt',
            'data/uploads/../../secret.txt'
        ]

        for path in vectors:
            with self.subTest(vector=path):
                result = _load_local_image(path)
                self.assertIsNone(result, f"Failed to block traversal for {path}")

    @patch('backend.openrouter.os.path.exists')
    def test_image_not_found(self, mock_exists):
        mock_exists.return_value = False
        result = _load_local_image("nonexistent.png")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
