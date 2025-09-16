import pytest
from fastapi.testclient import TestClient

# I need to import the 'app' object from the main file.
# This is tricky because of the file layout.
# I'll have to add the 'lexi_ai' directory to the sys.path.
import sys
import os

# Add the project root to the python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lexi_ai.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_read_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "LEXI-AI is running"}

def test_translate_text(client):
    """Test the /translate endpoint."""
    response = client.post(
        "/translate",
        json={"text": "This is a test.", "source_lang": "English", "target_lang": "Portuguese"}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "translated_text" in response_data
    # The response from the fake LLM is always the same
    assert response_data["translated_text"] == "This is a RAG-powered translated text."

def test_translate_text_missing_text(client):
    """Test the /translate endpoint with missing 'text' field."""
    response = client.post(
        "/translate",
        json={"source_lang": "English", "target_lang": "Portuguese"}
    )
    # FastAPI should return a 422 Unprocessable Entity for validation errors
    assert response.status_code == 422
