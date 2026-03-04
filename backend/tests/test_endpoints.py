import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import io

# Add backend to sys.path so we can import main, storage, etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a mock storage and council
mock_storage = MagicMock()
mock_council = MagicMock()

# Apply mocks to sys.modules BEFORE importing app to ensure they are used
with patch.dict(sys.modules, {
    "storage": mock_storage,
    "council": mock_council,
}):
    from main import app
    import config

@pytest.fixture
def client():
    """Fixture to provide a TestClient for the app."""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_mocks():
    """Fixture to reset mocks before each test."""
    mock_storage.reset_mock()
    mock_council.reset_mock()

def test_root(client):
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["product"] == "parallels"

def test_list_conversations(client):
    """Test listing conversations."""
    mock_storage.list_conversations.return_value = [
        {"id": "conv-1", "created_at": "2023-01-01T00:00:00", "title": "Test Title", "message_count": 2}
    ]
    response = client.get("/api/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "conv-1"
    mock_storage.list_conversations.assert_called_once()

def test_create_conversation_success(client):
    """Test successful conversation creation."""
    mock_storage.list_conversations.return_value = []
    mock_storage.create_conversation.return_value = {
        "id": "new-uuid",
        "created_at": "2023-01-01T00:00:00",
        "title": "New Task",
        "messages": []
    }
    response = client.post("/api/conversations", json={})
    assert response.status_code == 200
    assert response.json()["id"] == "new-uuid"
    mock_storage.create_conversation.assert_called_once()

def test_create_conversation_limit_reached(client):
    """Test conversation creation fails when limit is reached."""
    # Assuming MAX_CONVERSATIONS is 50
    mock_storage.list_conversations.return_value = [{"id": str(i)} for i in range(config.MAX_CONVERSATIONS)]
    response = client.post("/api/conversations", json={})
    assert response.status_code == 429
    assert "Maximum of" in response.json()["detail"]

def test_get_conversation_success(client):
    """Test getting a specific conversation."""
    mock_storage.get_conversation.return_value = {
        "id": "conv-1",
        "created_at": "2023-01-01T00:00:00",
        "title": "Test Title",
        "messages": []
    }
    response = client.get("/api/conversations/conv-1")
    assert response.status_code == 200
    assert response.json()["id"] == "conv-1"

def test_get_conversation_404(client):
    """Test getting a non-existent conversation."""
    mock_storage.get_conversation.return_value = None
    response = client.get("/api/conversations/missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "Exploration not found"

def test_delete_conversation_success(client):
    """Test successful conversation deletion."""
    mock_storage.delete_conversation.return_value = True
    response = client.delete("/api/conversations/conv-1")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_storage.delete_conversation.assert_called_with("conv-1")

def test_delete_conversation_404(client):
    """Test deleting a non-existent conversation."""
    mock_storage.delete_conversation.return_value = False
    response = client.delete("/api/conversations/missing")
    assert response.status_code == 404

def test_upload_file_success(client):
    """Test successful file upload."""
    file_content = b"fake image data"
    file_name = "test.png"
    # Mocking 'open' inside upload_file to avoid actual file creation
    with patch("main.open", create=True) as mock_open:
        response = client.post(
            "/api/upload",
            files={"file": (file_name, file_content, "image/png")}
        )
        assert response.status_code == 200
        assert "filename" in response.json()
        assert response.json()["content_type"] == "image/png"

def test_upload_file_invalid_type(client):
    """Test file upload with invalid type."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", b"some text", "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_upload_file_too_large(client):
    """Test file upload that exceeds size limit."""
    large_content = b"a" * (config.MAX_UPLOAD_SIZE + 1)
    response = client.post(
        "/api/upload",
        files={"file": ("large.png", large_content, "image/png")}
    )
    assert response.status_code == 400
    assert "File too large" in response.json()["detail"]

def test_send_message_stream_success(client):
    """Test streaming message endpoint (success)."""
    conversation_id = "conv-1"
    mock_storage.get_conversation.return_value = {
        "id": conversation_id,
        "messages": [] # Empty means it's the first message
    }

    # Mock council functions
    mock_council.run_analogy_pipeline = AsyncMock(return_value={
        "stages": {"stage2": "data", "stage3": "data"},
        "final_answer": "This is the final analogy."
    })
    mock_council.generate_conversation_title = AsyncMock(return_value="Analogy about X")

    response = client.post(
        f"/api/conversations/{conversation_id}/message/stream",
        json={"content": "Explain quantum physics using baking."}
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Verify storage was updated
    mock_storage.add_user_message.assert_called()
    mock_storage.add_assistant_message.assert_called()

def test_send_message_invalid_request(client):
    """Test message sending with invalid body."""
    response = client.post(
        "/api/conversations/conv-1/message/stream",
        json={"content": ""} # Empty content
    )
    assert response.status_code == 422 # Pydantic validation error
