# Tasks for 001-fastapi-api

## Phases

### Setup
- [ ] Add dependencies to pyproject (fastapi, uvicorn[standard])
- [ ] Create src/api/schemas.py and src/api/app.py skeletons

### Tests
- [ ] Unit tests for API: healthz returns ok
- [ ] Unit tests for API: POST /scrape validates URL (400)
- [ ] Unit tests for API: robots disallow maps to 403 (mock)
- [ ] Unit tests for API: happy path returns summary (mock)

### Core
- [ ] Implement schemas (ScrapeRequest, ScrapeSummary)
- [ ] Implement endpoints with logging and error mapping

### Integration
- [ ] Optional: wire Drive env (GDRIVE_SA_JSON) and drive_folder_id passthrough

### Polish
- [ ] README update for API usage
- [ ] Quick manual run instruction verified
