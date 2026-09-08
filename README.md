# Sentinel Command Dashboard

<div align="center">

**AI-driven CCTV command & control for the Sentinel Gujarat challenge**

[![Vercel Deploy](https://img.shields.io/badge/Vercel-deployed-000000?logo=vercel)](https://sentinel-gujarat.vercel.app)
[![Render Backend](https://img.shields.io/badge/Render-mock%20API-46E3B7?logo=render)](https://sentinel-command-demo-api.onrender.com)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776ab?logo=python)](https://www.python.org/)
[![CUDA 13.4](https://img.shields.io/badge/CUDA-13.4-76B900?logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![React 18](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev/)

</div>

---

## Overview

Edge-first CCTV command prototype that runs immediately in **deterministic mock mode** and switches to **live camera catalogue** when official credentials arrive.

### Key Features

- ✅ **Dynamic camera onboarding** from Sentinel `/api/ingest` catalogue  
- ✅ **Resilient RTSP-over-TCP** ingestion, PTS-based timing, exponential backoff  
- ✅ **Watchlist matching** and real-time alert creation  
- ✅ **GIS-based route reconstruction** and movement history  
- ✅ **GPU-accelerated inference** (YOLO, OCR, tracking on RTX 5050)  
- ✅ **Always-on mock deployment** via Vercel + Render  

---

## Architecture

### Mock Mode (Always-On)

```
Browser (Vercel)
    ↓
Vite Dashboard (React/MapLibre)
    ↓
Render API (Python/FastAPI)
    ↓
Seeded Mock Data
  • 4 demo cameras (Ahmedabad)
  • 5 alert history
  • 1 tracked entity
  • Operational GIS map
```

**Live**: https://sentinel-gujarat.vercel.app  
**API**: https://sentinel-command-demo-api.onrender.com  
**Status**: Laptop can be OFF. Mock data always available.

### Live Mode (Official Credentials Required)

```
Official Sentinel Gateway
    ↓
Laptop (RTSP Reader + GPU)
  • Real camera streams (RTSP/HLS)
  • YOLO detection (PyTorch/CUDA)
  • OCR license plates (EasyOCR)
  • Tracking (ByteTrack/Supervision)
    ↓
Cloudflare Tunnel
    ↓
Browser Dashboard
  • Live detections
  • Real-time alerts
  • Movement tracking
```

**Status**: Requires laptop ON. GPU processes real streams.

---

## Quick Start

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

Open `http://localhost:5173`  
With no `SENTINEL_CATALOGUE_URL`, the API creates mock cameras and events so every screen is usable.

---

## Deployment

### Online Mock Deployment (Already Live)

**Frontend**: https://sentinel-gujarat.vercel.app  
**Backend**: https://sentinel-command-demo-api.onrender.com  

See [docs/ONLINE_DEPLOYMENT.md](docs/ONLINE_DEPLOYMENT.md) for details.

### Live Integration (When Credentials Arrive)

Set only the values supplied by organizers in `.env`:

```env
SENTINEL_CATALOGUE_URL=https://cctv.corp8.cloud/cameras.json
SENTINEL_API_TOKEN=...
SENTINEL_USERNAME=...
SENTINEL_PASSWORD=...
SENTINEL_VERIFY_TLS=true
```

Then run:

```powershell
.\.venv\Scripts\python.exe backend\live_preflight.py --require-gpu
```

This validates the catalogue, lists available stream URLs, and verifies CUDA before starting the RTSP worker.

If the organizer's camera portal returns an HTML sign-in page instead of JSON, test a direct feed without using the catalogue:

```powershell
.\.venv\Scripts\python.exe backend\live_preflight.py --probe-camera cam04 --require-gpu
```

The direct probe builds the credentialed RTSP URL privately from `.env`, forces TCP, reads one frame, and never prints the URL or password.

Run a bounded YOLO GPU smoke test after the probe succeeds. The first connection can take several seconds to open, so use at least 30 seconds:

```powershell
.\.venv\Scripts\python.exe backend\live_inference_smoke.py --camera cam04 --seconds 30
```

This reports only the camera ID, GPU name, sampled frame count, and detection count. It does not publish alerts or expose credentials.

Run the complete live detector and tracker locally:

```powershell
python -m pip install -r backend/requirements-ai.txt
.\.venv\Scripts\python.exe backend\live_pipeline.py --camera cam04 --seconds 60
```

Add `--ocr` to enable EasyOCR. Add `--publish --latitude <LAT> --longitude <LNG>` only after the local API is running and `SENTINEL_INGEST_TOKEN` is set in `.env`; events are rate-limited per tracked entity.

---

## API Reference

### Health & Config
- `GET /health` — API status and mock mode indicator
- `GET /api/config/public` — Public dashboard configuration

### Camera Management
- `GET /api/cameras` — List loaded cameras  
- `POST /api/cameras/sync` — Fetch and validate from official catalogue (read-only)

### Detections & Alerts
- `GET /api/events` — Detection event history  
- `GET /api/alerts` — Priority alerts with watchlist matches
- `POST /api/events/ingest` — Token-protected edge detection metadata ingestion

### Tracking & Routes
- `GET /api/routes/{entity_id}` — Reconstructed GIS path for entity
- `GET /api/watchlist` — Current watchlist entries (stolen vehicles, wanted persons)
- `POST /api/watchlist` — Add watchlist entry

---

## Development

### Backend Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI endpoints
│   ├── config.py            # Settings & environment
│   ├── catalogue.py         # Sentinel API adapter
│   ├── models.py            # Data models (Camera, Event, Alert, etc.)
│   ├── inference.py         # RTSP worker & frame callback
│   └── streaming.py         # Reconnect policy, PTS timing
├── tests/
│   ├── test_catalogue.py    # Catalogue validation tests
│   └── test_streaming.py    # PTS timing & reconnect tests
├── requirements.txt         # Production dependencies
├── requirements-ai.txt      # Optional GPU/detection stack
└── live_preflight.py        # Tomorrow's first command
```

### Frontend Structure

```
frontend/
├── src/
│   ├── main.tsx            # React entry point
│   ├── App.tsx             # Dashboard shell & API client
│   ├── OperationalMap.tsx  # MapLibre GIS view
│   ├── VideoPreview.tsx    # Camera stream preview
│   └── styles.css          # Tailwind CSS
├── package.json            # Dependencies & build scripts
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript configuration
└── vercel.json             # Vercel build settings
```

### Running Tests

```powershell
cd path\to\sentinel-command
.\.venv\Scripts\Activate.ps1
python -m pytest backend/tests
```

### Installing Optional GPU Stack

For live RTSP processing:

```powershell
python -m pip install -r backend/requirements-ai.txt
```

This installs:
- `torch[cuda]` — PyTorch with CUDA support
- `ultralytics` — YOLO object detection
- `easyocr` — License plate OCR
- `supervision` — Tracking & annotation utilities
- `opencv-python` — Video I/O

---

## Operational Guarantees

- **RTSP TCP only**: UDP is never used; TCP ensures frame order and delivery.
- **PTS-based timing**: Processing time is read from source stream, never FPS or arrival time.
- **Decoder tolerance**: Brief H.264/H.265 warnings at stream start are normal and ignored.
- **Per-camera codec handling**: Each camera's codec, resolution, and framerate are preserved.
- **Resilient reconnect**: Exponential backoff from 2s to 30s on connection loss.
- **Read-only gateway access**: Only `/api/ingest` (read) is used; no control or publish endpoints.

---

## Documentation

- **[ONLINE_DEPLOYMENT.md](docs/ONLINE_DEPLOYMENT.md)** — Production deployment to Render + Vercel
- **[INTEGRATION_RUNBOOK.md](docs/INTEGRATION_RUNBOOK.md)** — Sentinel gateway integration checklist

---

## Security Notes

- **Credentials in `.env` only**: `SENTINEL_*` values must never be committed to Git or published to Vercel.
- **Public dashboard config**: Only `VITE_API_URL` (the public API endpoint) is embedded in the browser build.
- **Vercel environment**: No sensitive data belongs in Vercel; mock mode works without credentials.
- **GPU on laptop**: Live inference and GPU access remain local; never exposed online.

---

## License

This project is provided for the Sentinel Gujarat challenge. See individual components for attribution.

---

## Support

When reporting issues to organizer support, include:

- Camera ID (from `/api/cameras` or catalogue)
- Exact RTSP/HLS URL (from catalogue response)
- UTC timestamp and application version  
- Browser DevTools network log (redacted of credentials)
- Current `live` status from camera metadata
