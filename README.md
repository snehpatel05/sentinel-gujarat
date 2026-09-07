# Sentinel Command

An edge-first CCTV command prototype for the Sentinel Gujarat challenge. It runs immediately in a deterministic mock mode and switches to the official live catalogue when configuration is provided.

## What it demonstrates

- Dynamic camera onboarding from the Sentinel `/api/ingest` catalogue
- Resilient RTSP-over-TCP ingestion contract, PTS-based timing and reconnect backoff
- Watchlist matching, alert creation, searchable history and GIS route reconstruction
- HLS/WebRTC stream URLs from the catalogue; no hard-coded camera endpoint
- A configuration boundary for future VAHAN/SARTHI/eGujCop integrations

## Quick start

1. Copy `.env.example` to `.env`. Keep gateway credentials only in `.env`.
2. Start the API:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   uvicorn app.main:app --app-dir backend --reload --port 8000
   ```

3. In another terminal, start the dashboard:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

Open `http://localhost:5173`. With no `SENTINEL_CATALOGUE_URL`, the API creates mock cameras and events so every screen is usable.

## Connect the official sandbox later

Set only the values supplied by organizers in `.env`:

```env
SENTINEL_CATALOGUE_URL=http://HOST/api/ingest
SENTINEL_API_TOKEN=...
SENTINEL_USERNAME=...
SENTINEL_PASSWORD=...
```

Restart the backend, then click **Sync cameras** in the dashboard or call `POST /api/cameras/sync`. The adapter validates the response and stores the returned camera id, metadata, stream properties, and RTSP/HLS/WHEP URLs. It never derives URL paths from a camera id.

## Publish for online judging

Use Vercel for the public dashboard and Cloudflare Tunnel for the local GPU API. The complete, security-conscious sequence is in [`docs/ONLINE_DEPLOYMENT.md`](docs/ONLINE_DEPLOYMENT.md). Keep Sentinel credentials on the laptop; only `VITE_API_URL` (the public API endpoint) belongs in Vercel.

## Operational guarantees in the codebase

- RTSP clients are configured for TCP.
- Processing time is based on source PTS, never reported FPS or frame-arrival time.
- Mixed H.264/H.265 streams and non-fatal decoder-start warnings are tolerated.
- Reconnects use capped exponential backoff.
- Every live gateway call is read-only; no publish/control endpoint is used.

## API reference

`GET /health` · `GET /api/cameras` · `POST /api/cameras/sync` · `GET /api/events` · `GET /api/alerts` · `GET /api/routes/{entity_id}` · `GET/POST /api/watchlist` · `GET /api/config/public`
