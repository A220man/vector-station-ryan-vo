import pytest
from httpx import AsyncClient
from passlib.context import CryptContext
from sqlalchemy import select
from app.models import Voice, VoiceType


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


@pytest.mark.asyncio
async def test_upload_reference_audio(client, db_session, auth_headers):
    """Test uploading reference audio for voice cloning.
    
    Tests the upload-reference endpoint that accepts reference audio files
    for cloned voices. Verifies the file is stored and the voice's
    reference_audio_path is updated.
    """
    import uuid
    from pathlib import Path
    from app.core.config import get_settings
    
    # Create a minimal WAV audio file header
    # WAV: RIFF chunk + fmt subchunk + data subchunk
    wav_data = (
        b'RIFF' +
        (36 + 1000).to_bytes(4, 'little') +
        b'WAVE' +
        b'fmt ' +
        (16).to_bytes(4, 'little') +
        (1).to_bytes(2, 'little') +  # audio format (PCM)
        (1).to_bytes(2, 'little') +  # number of channels
        (22050).to_bytes(4, 'little') +  # sample rate
        (22050 * 2 * 1).to_bytes(4, 'little') +  # byte rate
        (2).to_bytes(2, 'little') +  # block align
        (16).to_bytes(2, 'little') +  # bits per sample
        b'data' +
        (1000).to_bytes(4, 'little') +
        b'\x00' * 1000  # 1000 bytes of silence
    )
    
    # First create a cloned voice
    voice = Voice(
        name='TestCloneVoice',
        description='Voice for cloning test',
        voice_type=VoiceType.CLONED,
        language='en',
        sample_rate=22050,
        is_active=1,
        owner_id=1,
    )
    db_session.add(voice)
    await db_session.commit()
    await db_session.refresh(voice)
    
    filename = f'test_ref_{uuid.uuid4().hex}.wav'
    
    files = {'file': (filename, wav_data, 'audio/wav')}
    data = {'voice_id': str(voice.id)}
    
    response = await client.post(
        f'/api/voices/{voice.id}/upload-reference',
        files=files,
        data=data,
        headers=auth_headers,
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    response_data = response.json()
    assert 'reference_audio_path' in response_data
    assert response_data['reference_audio_path'] is not None
    
    # Verify the voice was updated in the database
    await db_session.refresh(voice)
    assert voice.reference_audio_path is not None
    assert voice.reference_audio_path.endswith('.wav')
    
    # Verify the file exists somewhere in the upload directory
    upload_dir = Path(get_settings().upload_dir) / "reference_audio"
    expected_filename = voice.reference_audio_path.split('/')[-1]
    found = False
    if upload_dir.exists():
        for f in upload_dir.iterdir():
            if f.name == expected_filename:
                found = True
                break
    assert found, f"Expected file {expected_filename} to be in {upload_dir}"
