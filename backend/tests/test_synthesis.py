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