# Contributing

This project is developed for the Sentinel Gujarat challenge.

## Development Setup

1. **Clone the repository**:
   ```powershell
   git clone https://github.com/snehpatel05/sentinel-gujarat.git
   cd sentinel-gujarat
   ```

2. **Create a Python virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r backend/requirements.txt
   cd frontend && npm install && cd ..
   ```

## Running Locally

### Backend
```powershell
uvicorn app.main:app --app-dir backend --reload --port 8000
```

### Frontend
```powershell
cd frontend
npm run dev
```

### Tests
```powershell
python -m pytest backend/tests -v
```

## Code Guidelines

- **Python**: Use `black` for formatting and `pytest` for tests.
- **TypeScript**: Use Prettier and ESLint from the Vite config.
- **Secrets**: Never commit `.env`, API tokens, or credentials.
- **RTSP**: Always use TCP; UDP is not supported.
- **Timing**: Use PTS from stream, never frame-arrival time.

## Before Submitting

1. Run tests locally.
2. Test against mock data (no credentials needed).
3. Verify `/health` endpoint returns `200`.
4. Ensure `.env` is never committed.
5. Document any new environment variables in `.env.example`.

## Reporting Issues

Include:
- Steps to reproduce
- Camera ID and timestamp (if applicable)
- Network requests (redacted of credentials)
- Python/Node version and OS
