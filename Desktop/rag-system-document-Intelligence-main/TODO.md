# TODO - Tweak RAG system for Docker Compose / Windows

- [ ] Inspect backend service code for CHROMA connection + upload path assumptions
- [ ] Inspect backend Dockerfile for workdir/ports and entrypoint
- [ ] Fix `rag/backend/main.py` to remove duplicated stacked blocks (keep a single valid FastAPI app)
- [ ] Fix uploads path to work with Docker volume mounts (`./uploads` -> `/app/uploads`)
- [ ] Fix docker-compose CHROMA port mismatch (backend `CHROMA_PORT` should match chroma container port)
- [ ] Add/verify required env var loading (GEMINI_API_KEY, CHROMA_HOST/PORT)
- [ ] Update README with Docker run instructions and required env vars
- [ ] Test: `docker compose up --build`
- [ ] Test endpoints: `/health`, `/upload`, `/chat`

