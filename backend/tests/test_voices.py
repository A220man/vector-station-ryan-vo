import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_voices(client: AsyncClient, auth_headers, builtin_voice):
    response = await client.get("/api/voices", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(v["name"] == "Test Voice" for v in data["voices"])


@pytest.mark.asyncio
async def test_get_voice(client: AsyncClient, auth_headers, builtin_voice):
    response = await client.get(f"/api/voices/{builtin_voice.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == builtin_voice.id
    assert data["name"] == "Test Voice"
    assert data["voice_type"] == "builtin"


@pytest.mark.asyncio
async def test_create_voice_requires_operator_role(client: AsyncClient, db_session):
    # Create a viewer user
    from app.models import User, UserRole
    from app.core.security import get_password_hash, create_access_token
    
    viewer = User(
        email="viewer@test.com",
        username="viewer",
        hashed_password=get_password_hash("pass"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(viewer)
    await db_session.commit()
    await db_session.refresh(viewer)
    
    viewer_token = create_access_token(subject=str(viewer.id), roles=[UserRole.VIEWER.value])
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    
    response = await client.post(
        "/api/voices",
        json={"name": "New Voice", "voice_type": "cloned", "reference_audio_path": "/tmp/test.wav"},
        headers=viewer_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_voice_success(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/voices",
        json={
            "name": "Cloned Voice",
            "description": "A cloned voice",
            "voice_type": "cloned",
            "language": "en",
            "reference_audio_path": "/tmp/reference.wav",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cloned Voice"
    assert data["voice_type"] == "cloned"
    assert data["reference_audio_path"] == "/tmp/reference.wav"


@pytest.mark.asyncio
async def test_create_cloned_voice_requires_reference(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/voices",
        json={"name": "Cloned Voice", "voice_type": "cloned"},
        headers=auth_headers,
    )
    assert response.status_code == 422