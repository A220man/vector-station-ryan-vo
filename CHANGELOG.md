# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-14

### Added
- FastAPI backend with modular architecture (core, models, schemas, api, services, db)
- SQLite persistent storage with SQLAlchemy 2.0 async ORM
- Voice management: built-in, cloned, and designed voice types
- Text-to-speech synthesis workflow with async job queue
- JWT authentication with local dev mode and OIDC/Keycloak production support
- Role-based access control (viewer, operator, admin)
- React 18 + TypeScript + Vite frontend
- Dashboard with TTS form, voice selection, audio playback, job history
- Voices management page with CRUD operations
- Login page with local auth and OIDC initiation
- Typed API client with automatic token refresh
- Dockerfiles for backend and frontend (non-root users)
- Docker Compose with backend, frontend, and Keycloak services
- Keycloak realm export with pre-configured client, roles, and PKCE
- Comprehensive test suite (backend: health, auth, voices, synthesis; frontend: dashboard)
- OpenAPI documentation at `/docs`
- Health and readiness endpoints for orchestration
- CORS configuration for local development

### Security
- HttpOnly SameSite cookies for session storage (OIDC flow)
- PKCE enforcement for authorization code flow
- JWT signature/issuer/audience validation
- SQL injection prevention via parameterized queries
- Input validation on all API endpoints
- No hardcoded secrets; all credentials via environment variables

### Documentation
- README with architecture diagram, API reference, quick start
- AI/ML evaluation section with reproducible baseline
- Security limitations and production checklist
- SSO/SAML setup instructions
- Portfolio metadata (portfolio.json)

## [Unreleased]

### Planned
- Voice cloning from reference audio (embedding extraction)
- Video dubbing workflow (extract, transcribe, translate, synthesize, recombine)
- Speech-to-text transcription with timestamps
- Audiobook creation with multi-chapter support
- Voice design from parameters (procedural generation)
- Neural TTS model integration (Piper, Coqui, Bark)
- Streaming synthesis for long-form content
- PostgreSQL production configuration
- Rate limiting and API throttling
- Comprehensive logging and monitoring