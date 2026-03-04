import pytest
import time
from unittest.mock import patch
from backend.main import RateLimiter

class TestRateLimiter:
    @pytest.fixture
    def limiter(self):
        return RateLimiter()

    def test_initial_state(self, limiter):
        """Test that a new limiter has no requests."""
        assert len(limiter._requests) == 0

    @patch('backend.main.time.time')
    def test_is_allowed_basic(self, mock_time, limiter):
        """Test basic allowance within limit."""
        mock_time.return_value = 1000.0

        # Limit 5, making 1 request -> Allowed
        assert limiter.is_allowed("1.2.3.4", "test", 5) is True
        assert limiter.remaining("1.2.3.4", "test", 5) == 4

    @patch('backend.main.time.time')
    def test_is_allowed_limit_reached(self, mock_time, limiter):
        """Test that requests are blocked when limit is reached."""
        mock_time.return_value = 1000.0
        limit = 3

        # Fill the limit
        for _ in range(limit):
            assert limiter.is_allowed("1.2.3.4", "test", limit) is True

        # Next request should be blocked
        assert limiter.is_allowed("1.2.3.4", "test", limit) is False
        assert limiter.remaining("1.2.3.4", "test", limit) == 0

    @patch('backend.main.time.time')
    def test_window_expiry(self, mock_time, limiter):
        """Test that old requests are cleaned up and new ones allowed."""
        # Start at time 1000
        mock_time.return_value = 1000.0
        limit = 2

        # Fill limit
        limiter.is_allowed("1.2.3.4", "test", limit)
        limiter.is_allowed("1.2.3.4", "test", limit)
        assert limiter.is_allowed("1.2.3.4", "test", limit) is False

        # Move time forward by 61 seconds (window is 60s by default)
        mock_time.return_value = 1061.0

        # Should be allowed again as old requests expired
        assert limiter.is_allowed("1.2.3.4", "test", limit) is True
        # Only 1 request in current window now
        assert limiter.remaining("1.2.3.4", "test", limit) == 1

    @patch('backend.main.time.time')
    def test_multiple_categories(self, mock_time, limiter):
        """Test that limits are independent for different categories."""
        mock_time.return_value = 1000.0
        limit = 1

        # Block "cat1"
        limiter.is_allowed("1.2.3.4", "cat1", limit)
        assert limiter.is_allowed("1.2.3.4", "cat1", limit) is False

        # "cat2" should still be allowed
        assert limiter.is_allowed("1.2.3.4", "cat2", limit) is True

    @patch('backend.main.time.time')
    def test_multiple_ips(self, mock_time, limiter):
        """Test that limits are independent for different IPs."""
        mock_time.return_value = 1000.0
        limit = 1

        # Block IP1
        limiter.is_allowed("1.2.3.4", "test", limit)
        assert limiter.is_allowed("1.2.3.4", "test", limit) is False

        # IP2 should still be allowed
        assert limiter.is_allowed("5.6.7.8", "test", limit) is True

    @patch('backend.main.time.time')
    def test_remaining_accuracy(self, mock_time, limiter):
        """Test remaining calculation."""
        mock_time.return_value = 1000.0
        limit = 10

        assert limiter.remaining("1.2.3.4", "test", limit) == 10

        limiter.is_allowed("1.2.3.4", "test", limit)
        assert limiter.remaining("1.2.3.4", "test", limit) == 9

        limiter.is_allowed("1.2.3.4", "test", limit)
        assert limiter.remaining("1.2.3.4", "test", limit) == 8

    @patch('backend.main.time.time')
    def test_clean_old_explicit(self, mock_time, limiter):
        """Test internal cleanup logic explicitly."""
        mock_time.return_value = 1000.0
        key = "1.2.3.4:test"

        # Add requests manually to internal structure for precise control
        limiter._requests[key] = [900, 950, 1000] # 900 is old (limit 60s -> cutoff 940)

        # Calling _clean_old with current time 1000
        limiter._clean_old(key, window=60)

        # 900 should be gone. 950 and 1000 remain.
        assert limiter._requests[key] == [950, 1000]

    @patch('backend.main.time.time')
    def test_sliding_window_edge(self, mock_time, limiter):
        """Test requests exactly at the edge of the window."""
        # Window is 60s.

        mock_time.return_value = 1000.0
        limiter.is_allowed("1.2.3.4", "test", 10)

        # At 1060: cutoff = 1000. Request (1000) > 1000 is False. Request removed.
        mock_time.return_value = 1060.0
        assert limiter.remaining("1.2.3.4", "test", 10) == 10

        # Let's double check with T=1059.9. Cutoff = 999.9. 1000 > 999.9 is True. Request kept.
        # Reset for this part
        limiter = RateLimiter() # New instance
        mock_time.return_value = 1000.0
        limiter.is_allowed("1.2.3.4", "test", 10)

        mock_time.return_value = 1059.9
        assert limiter.remaining("1.2.3.4", "test", 10) == 9
