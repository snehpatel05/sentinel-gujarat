# Sentinel Command

<div align="center">

**A GPU-assisted CCTV operations console for the Sentinel Gujarat challenge.**

[![Frontend](https://img.shields.io/badge/frontend-Vercel-111827?logo=vercel)](https://sentinel-gujaratvercel.app)
[![Backend](https://img.shields.io/badge/backend-Render-46e3b7?logo=render)](https://sentinel-gujaratvercel-ggt2.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.14-3776ab?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-TypeScript-149eca?logo=react)](https://react.dev/)
[![CUDA](https://img.shields.io/badge/CUDA-RTX%205050-76b900?logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)

</div>

---

## Current Status

| Area | Status | What it means |
|---|---|---|
| Formal dashboard UI | Ready | Operations-console frontend is built and published |
| Local FastAPI service | Ready | Runs on `127.0.0.1:8000` |
| Local GPU model | Ready | YOLO + ByteTrack verified on the RTX 5050 |
| Event ingestion | Ready | Token-protected metadata endpoint is implemented |
| Deployed demonstration | Ready | Vercel + Render serve seeded demonstration data |
| Organizer camera gateway | Blocked upstream | Gateway currently returns `502 Bad Gateway` and RTSP ports are unreachable |

**Important:** the project code is ready. Real camera results cannot appear until the organizer gateway becomes reachable again. That is an external service issue, not a local model failure.

---

## What This Project Does

Sentinel Command turns camera video into an operator-friendly incident picture:

```text
Camera stream
    |
    v
RTSP over TCP
    |
    v
YOLO object detection
    |
    v
ByteTrack identity tracking
    |
    +--> Optional EasyOCR plate/text recognition
    |
    v
Watchlist matching
    |
    v
Events, alerts, and movement routes
    |
    v
Operations dashboard
```

The system sends compact detection metadata to the API. It does not upload or publish raw video frames.

### Example Detection Event

```json
{
  "camera_id": "cam04",
  "entity_id": "cam04:12",
  "entity_type": "car",
  "plate": null,
  "occurred_at": "2026-09-09T10:30:00Z",
  "source_pts_ms": 18420,
  "confidence": 0.91,
  "location": {
    "latitude": 23.03,
    "longitude": 72.56
  }
}
```

### Example Operator Outcome

A detected plate that matches an active watchlist item becomes:

```text
Detection -> watchlist match -> priority alert -> map event -> route history
```

---

## Two Operating Modes

### 1. Deployed Demonstration

```text
Browser
  -> Vercel dashboard
  -> Render API
  -> Seeded cameras, events, alerts, and routes
```

Open: **https://sentinel-gujaratvercel.app**

This mode is designed for a stable presentation. It works without your laptop, private credentials, GPU, or camera gateway.

### 2. Local Live-AI Mode

```text
Camera gateway
  -> Your laptop
  -> RTSP worker
  -> RTX 5050
  -> YOLO + ByteTrack + optional OCR
  -> Local FastAPI
  -> Local dashboard
```

Open: **http://127.0.0.1:5173**

This mode is the technically meaningful version. It uses the local GPU and is ready to process real RTSP streams when the organizer gateway is online.

---

## Use the Local Model

### Start the local API

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Check it:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
```

### Start the dashboard

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173**.

The local frontend uses `frontend/.env.local` and points to `http://127.0.0.1:8000`.

### Check one camera

Use a camera ID such as `cam04`:

```powershell
.\.venv\Scripts\python.exe backend\live_preflight.py --probe-camera cam04 --require-gpu
```

A successful result looks like:

```text
RTSP probe: cam04 (TCP)
Frame: received (1920x1080)
GPU: ready (NVIDIA GeForce RTX 5050 Laptop GPU)
Direct RTSP preflight passed.
```

### Run the local detector without publishing

This is the safest normal test:

```powershell
.\.venv\Scripts\python.exe backend\live_pipeline.py --camera cam04 --seconds 60
```

It runs YOLO and ByteTrack locally and reports frames and tracked objects. It does not publish events.

### Run optional OCR

```powershell
.\.venv\Scripts\python.exe backend\live_pipeline.py --camera cam04 --seconds 60 --ocr
```

The first OCR run may download model files. Those files remain local and are ignored by Git.

### Publish detection metadata locally

Set this only in your private `.env`:

```env
SENTINEL_INGEST_TOKEN=your-long-private-token
```

Start the API, then run:

```powershell
.\.venv\Scripts\python.exe backend\live_pipeline.py `
  --camera cam04 `
  --seconds 60 `
  --publish `
  --latitude 23.03 `
  --longitude 72.56
```

The API creates events and checks active watchlist entries. Publishing requires the token and fails closed when it is missing.

### Stop everything

In each running terminal, press:

```text
Ctrl+C
```

The virtual environment itself does not run in the background after VS Code closes.

---

## Camera Feed Configuration

The organizer-provided format is:

```text
HLS:  https://cctv.corp8.cloud/<id>/index.m3u8
RTSP: rtsp://<encoded-email>:<password>@103.250.160.189:8554/stream/<id>
WHEP: http://103.250.160.189:8889/stream/<id>/whep
```

Camera IDs are expected to look like `cam01` through `cam30`.

The local `.env` contains the private username and password. The application percent-encodes the email address and never sends the credential-bearing RTSP URL to the browser.

Do not commit or paste `.env` contents. Use `.env.example` as the safe template.

---

## Why the Live Website May Not Show Real Cameras

The public dashboard and the live camera gateway are separate services.

The current external failure is:

```text
https://cctv.corp8.cloud/cameras.json -> 502 Bad Gateway
103.250.160.189:8554 -> unreachable from the current network
103.250.160.189:8889 -> unreachable from the current network
```

When the organizer gateway is restored, retry:

```powershell
.\.venv\Scripts\python.exe backend\live_preflight.py --probe-camera cam04 --require-gpu
```

No code redesign should be needed for that recovery. If the organizer changes authentication or endpoints, update only `.env` and the integration adapter.

---

## API Surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service and mode status |
| `GET` | `/api/config/public` | Safe frontend configuration |
| `GET` | `/api/cameras` | Public camera records without RTSP credentials |
| `POST` | `/api/cameras/sync` | Read-only catalogue synchronization |
| `GET` | `/api/events` | Detection history |
| `POST` | `/api/events/ingest` | Token-protected edge metadata ingestion |
| `GET` | `/api/alerts` | Priority alerts |
| `GET` | `/api/routes/{entity_id}` | Entity movement route |
| `GET` | `/api/watchlist` | Active watchlist |
| `POST` | `/api/watchlist` | Add a watchlist entry |

Interactive API documentation is available at **http://127.0.0.1:8000/docs** when the local API is running.

---

## Verification

Run the backend tests:

```powershell
$env:PYTHONPATH = "backend"
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Build the frontend:

```powershell
cd frontend
npm run build
```

The repository currently has tests for:

- Catalogue field normalization
- Direct stream URL generation
- RTSP TCP and PTS timing
- Reconnect backoff
- Protected event ingestion
- Direct-camera registration

---

## Project Layout

```text
backend/
├── app/
│   ├── catalogue.py       # Catalogue adapter and stream URL generation
│   ├── config.py          # Environment-backed settings
│   ├── inference.py       # RTSP worker with PTS sampling
│   ├── main.py            # FastAPI API and event ingestion
│   ├── models.py          # API data models
│   └── streaming.py       # TCP transport and reconnect policy
├── live_pipeline.py       # YOLO + ByteTrack + optional OCR runner
├── live_preflight.py      # Camera and CUDA readiness checks
└── tests/                 # Backend tests
frontend/
├── src/
│   ├── App.tsx            # Operations console
│   ├── OperationalMap.tsx # Map and camera markers
│   ├── VideoPreview.tsx   # HLS preview
│   └── styles.css         # Formal console theme
└── package.json
```

---

## Security Rules

- Keep `.env` on the laptop only.
- Never paste passwords, tokens, RTSP URLs, or session cookies into chat.
- Never put Sentinel credentials in Vercel or frontend code.
- The browser receives HLS/WHEP URLs only; credential-bearing RTSP stays server-side.
- Event ingestion rejects requests without `SENTINEL_INGEST_TOKEN`.
- Raw video is processed at the edge and is not uploaded by the live pipeline.

---

## Documentation

- [Online deployment guide](docs/ONLINE_DEPLOYMENT.md)
- [Live integration runbook](docs/INTEGRATION_RUNBOOK.md)
- [Contributing guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## License

This project is provided for the Sentinel Gujarat challenge. See [LICENSE](LICENSE).
