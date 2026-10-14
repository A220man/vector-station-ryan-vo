# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-skeleton-tts

## Roadmap

### core-skeleton-tts — Core Skeleton + Text-to-Speech Workflow

Status: done

Acceptance:
- FastAPI backend runs with /health endpoint
- React + Vite frontend builds and loads
- SQLite database initializes with voice and synthesis tables
- TTS synthesis endpoint accepts text and returns audio (WAV/MP3)
- Frontend dashboard allows text input, voice selection, and audio playback
- Basic OIDC authentication structure in place (Keycloak-ready)
- Dockerfiles and compose.yaml for local development
- Backend tests: health, TTS endpoint, database models
- Frontend tests: dashboard renders, TTS form submits

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `backend/app/core/exceptions.py`, `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`, `backend/app/api/deps.py`, `backend/app/api/router.py`, `backend/app/api/routes/health.py`, `backend/app/api/routes/voices.py`, `backend/app/api/routes/synthesis.py`, `backend/app/api/routes/auth.py`, `backend/app/services/tts.py`, `backend/app/db/init_db.py`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/pyproject.toml`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/components/AudioPlayer.tsx`, `frontend/src/components/VoiceSelector.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Voices.tsx`, `frontend/src/pages/Login.tsx`, `frontend/src/hooks/useAuth.ts`, `frontend/src/hooks/useSynthesis.ts`, `frontend/src/api/client.ts`, `frontend/src/types/api.ts`, `frontend/src/styles/globals.css`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/Dockerfile`, `frontend/nginx.conf`, `compose.yaml`, `keycloak/realm-export.json`, `.env.example`, `.gitignore`, `README.md`, `LICENSE`, `CHANGELOG.md`, `portfolio.json`, `.github/workflows/ci.yml`

Tests: `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_voices.py`, `backend/tests/test_synthesis.py`, `backend/tests/test_auth.py`, `frontend/src/test/setup.ts`, `frontend/src/pages/Dashboard.test.tsx`

### voice-cloning — Voice Cloning from Reference Audio

Status: planned

Acceptance:
- Upload reference audio endpoint
- Voice embedding extraction and storage
- Cloned voice available for TTS synthesis
- Frontend voice cloning workflow with upload and preview

### video-dubbing — Video Dubbing Workflow

Status: planned

Acceptance:
- Video upload and audio extraction
- Transcription of original audio
- Translation (optional LLM-assisted)
- Dubbed audio synthesis and video recombination
- Frontend dubbing workflow

### transcription — Speech-to-Text Transcription

Status: planned

Acceptance:
- Audio upload and transcription endpoint
- Segmented output with timestamps
- Export as SRT/VTT/TXT
- Frontend transcription viewer

### audiobook-creation — Audiobook Creation with Chapters

Status: planned

Acceptance:
- Multi-chapter project structure
- Per-chapter voice assignment
- Batch synthesis with progress tracking
- Export as single audio file or chapters

### voice-design — Voice Design from Parameters

Status: planned

Acceptance:
- Voice parameter controls (pitch, speed, timbre, etc.)
- Procedural voice generation
- Save designed voices for reuse

### auth-oidc-complete — Complete OIDC/Keycloak Authentication

Status: planned

Acceptance:
- Keycloak realm import configuration
- Authorization code flow with PKCE
- Role-based access control (viewer, operator, admin)
- Protected API endpoints
- Frontend login/logout flow

