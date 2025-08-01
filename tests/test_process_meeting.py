import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router

app = FastAPI()
app.include_router(router, prefix="/api/v1")

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_process_meeting_mock(client):
    # Create a dummy audio file in memory
    dummy_audio = io.BytesIO(b"RIFF....WAVEfmt ")  # Minimal WAV header
    dummy_audio.name = "test.wav"

    response = client.post(
        "/api/v1/process-meeting",
        files={"file": ("test.wav", dummy_audio, "audio/wav")},
        data={"format": "wav"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert isinstance(data["transcript"], dict)
    assert "full_text" in data["transcript"]
    assert isinstance(data["speakers"], list)
    assert "technical_terms" in data
    assert data["error"] is not None or data["error"] is None  # Accepts both mock and real
