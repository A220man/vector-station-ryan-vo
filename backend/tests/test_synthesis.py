import asyncio
import os
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_synthesis(client: AsyncClient, auth_headers, builtin_voice):
    response = await client.post(
        "/api/synthesis",
        json={
            "text": "Hello, this is a test synthesis.",
            "voice_id": builtin_voice.id,
            "speed": 100,
            "pitch": 0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "Hello, this is a test synthesis."
    assert data["voice_id"] == builtin_voice.id
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_synthesis_invalid_voice(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/synthesis",
        json={
            "text": "Test",
            "voice_id": 99999,
        },
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_synthesis_jobs(client: AsyncClient, auth_headers, builtin_voice):
    # Create a job first
    await client.post(
        "/api/synthesis",
        json={"text": "Test job", "voice_id": builtin_voice.id},
        headers=auth_headers,
    )

    response = await client.get("/api/synthesis", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_synthesis_job(client: AsyncClient, auth_headers, builtin_voice):
    create_resp = await client.post(
        "/api/synthesis",
        json={"text": "Test job detail", "voice_id": builtin_voice.id},
        headers=auth_headers,
    )
    job_id = create_resp.json()["id"]

    response = await client.get(f"/api/synthesis/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["text"] == "Test job detail"


@pytest.mark.asyncio
async def test_synthesis_text_validation(client: AsyncClient, auth_headers, builtin_voice):
    # Empty text
    response = await client.post(
        "/api/synthesis",
        json={"text": "", "voice_id": builtin_voice.id},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Too long text
    long_text = "x" * 6000
    response = await client.post(
        "/api/synthesis",
        json={"text": long_text, "voice_id": builtin_voice.id},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_download_audio_mp3_format(client: AsyncClient, auth_headers, builtin_voice, db_session):
    """Test that audio download works with MP3 output format."""
    # Temporarily set MP3 format
    original_format = os.environ.get("AUDIO_OUTPUT_FORMAT")
    os.environ["AUDIO_OUTPUT_FORMAT"] = "mp3"

    try:
        # Need to reload settings for the new format
        from app.core.config import get_settings

        get_settings.cache_clear()

        # Create synthesis job
        response = await client.post(
            "/api/synthesis",
            json={
                "text": "Test MP3 synthesis",
                "voice_id": builtin_voice.id,
                "speed": 100,
                "pitch": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        job_id = response.json()["id"]
        # Process synthesis directly (since background tasks are skipped in tests)
        from app.api.routes.synthesis import process_synthesis_job
        from tests.conftest import TestAsyncSessionMaker
        await process_synthesis_job(job_id, TestAsyncSessionMaker)

        # Verify job completed
        job_resp = await client.get(f"/api/synthesis/{job_id}", headers=auth_headers)
        assert job_resp.status_code == 200
        job = job_resp.json()
        assert job["status"] == "completed"
        assert job["output_path"] is not None

        # Download audio
        audio_resp = await client.get(f"/api/synthesis/{job_id}/audio", headers=auth_headers)
        assert audio_resp.status_code == 200
        assert audio_resp.headers["content-type"] == "audio/mpeg"
        assert f"synthesis_{job_id}.mp3" in audio_resp.headers.get("content-disposition", "")
        assert len(audio_resp.content) > 0
    finally:
        # Restore original format
        if original_format is not None:
            os.environ["AUDIO_OUTPUT_FORMAT"] = original_format
        else:
            os.environ.pop("AUDIO_OUTPUT_FORMAT", None)
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_download_audio_wav_format(client: AsyncClient, auth_headers, builtin_voice, db_session):
    """Test that audio download works with WAV output format (default)."""
    # Ensure WAV format
    original_format = os.environ.get("AUDIO_OUTPUT_FORMAT")
    os.environ["AUDIO_OUTPUT_FORMAT"] = "wav"

    try:
        from app.core.config import get_settings

        get_settings.cache_clear()

        # Create synthesis job
        response = await client.post(
            "/api/synthesis",
            json={
                "text": "Test WAV synthesis",
                "voice_id": builtin_voice.id,
                "speed": 100,
                "pitch": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        job_id = response.json()["id"]

        # Process synthesis directly (since background tasks are skipped in tests)
        from app.api.routes.synthesis import process_synthesis_job
        from tests.conftest import TestAsyncSessionMaker
        await process_synthesis_job(job_id, TestAsyncSessionMaker)

        # Verify job completed
        job_resp = await client.get(f"/api/synthesis/{job_id}", headers=auth_headers)
        assert job_resp.status_code == 200
        job = job_resp.json()
        assert job["status"] == "completed"
        assert job["output_path"] is not None

        # Download audio
        audio_resp = await client.get(f"/api/synthesis/{job_id}/audio", headers=auth_headers)
        assert audio_resp.status_code == 200
        assert audio_resp.headers["content-type"] == "audio/wav"
        assert f"synthesis_{job_id}.wav" in audio_resp.headers.get("content-disposition", "")
        assert len(audio_resp.content) > 0
    finally:
        if original_format is not None:
            os.environ["AUDIO_OUTPUT_FORMAT"] = original_format
        else:
            os.environ.pop("AUDIO_OUTPUT_FORMAT", None)
        get_settings.cache_clear()

