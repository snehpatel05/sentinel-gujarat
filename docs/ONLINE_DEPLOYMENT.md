# Online Deployment: Vercel + Render + Cloudflare Tunnel

## Overview

**Always-on mock API**: Dashboard + seeded data deployed to Vercel + Render (laptop OFF)  
**Live integration**: Real camera streams via Cloudflare Tunnel when credentials arrive (laptop ON + GPU)

The dashboard is a static Vercel site. GPU, private Sentinel credentials, and RTSP ingestion stay on the RTX laptop. A Cloudflare Tunnel makes only the HTTP API reachable to the dashboard. **Never put `SENTINEL_*` secrets in Vercel.**

## Architecture

### Always-On Mock (Current)

```
Judge Browser
    ↓
https://sentinel-gujaratvercel.app (Vercel)
    ↓
https://sentinel-gujaratvercel-ggt2.onrender.com (Render Mock API)
    ↓
Seeded Cameras & History
```

**Status**: Live without laptop. Demo camera feeds and alert history always available.

### Live Integration (When Credentials Arrive)

```
Judge Browser
    ↓
https://sentinel-gujaratvercel.app (Vercel)
    ↓
https://api.sentinel-live.yourname.example (Cloudflare Tunnel)
    ↓
Laptop:8000 (GPU + RTSP Reader)
    ↓
Official Sentinel Gateway
    ↓
Real Camera Streams
```

**Status**: Requires laptop ON, connected to internet, running API + tunnel.

## Always-On Mock API (Already Live)

✅ **Deployed to Render**: https://sentinel-gujaratvercel-ggt2.onrender.com  
✅ **Frontend on Vercel**: https://sentinel-gujaratvercel.app  
✅ *Prerequisites for Live Integration (When Credentials Arrive)

Install once on the RTX laptop:

- ✅ **Python 3.14** (already installed)
- ✅ **Node.js** (already installed)
- ✅ **Git for Windows** — [Download](https://git-scm.com/download/win)
- ✅ **Cloudflare Tunnel** — [Download `cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
- 📦 **FFmpeg** (optional but recommended) — [Download](https://ffmpeg.org/download.html)
- 🔧 **GPU AI Stack** (optional, only if processing live RTSP):
  ```powershell
  pip install -r backend/requirements-ai.txt
  ```
2. Git for Windows: <https://git-scm.com/download/win>
3. CloudfDevelopment (Before Going Online)

### Backend Setup

```powershell
cd path\to\sentinel-command
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### Frontend Setup (New Terminal)

```powershell
cd path\to\sentinel-command\frontend
npm install
npm run dev
```

### Verify Local Setup

- Dashboard: http://localhost:5173
- API: http://localhost:8000/health
- Inspect mock cameras: http://localhost:8000/api/cameras

Before exposing online, confirm all endpoints work locally
npm run dev
```

Verify `http://localhost:5173` before exposing anything online.

## Exposing the Backend Safely (Live Integration Phase)

### Option 1: Rehearsal Link (Temporary, One-Command)

While the API is running on port 8000:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

**Output**: A random `https://…trycloudflare.com` address (changes on each run).  
**Use case**: Rehearsal and testing only, not for final judging.

### Option 2: Stable Judging Link (Persistent Domain)

1. Create a **free Cloudflare account** at https://cloudflare.com
2. **Add your domain** (e.g., `example.com`) to Cloudflare DNS
3. In Cloudflare dashboard → **Tunnels** → Create a named tunnel
4. Map a hostname (e.g., `api.example.com`) to `http://127.0.0.1:8000`
5. Cloudflare provides a **tunnel command** with a token. Run it on the laptop:

   ```powershell
   cloudflared service install <TOKEN>
   ```

   (Or run without `service install` for testing)

6. Update the laptop's `.env`:

   ```env
   SENTINEL_CORS_ORIGINS=https://your-vercel-project.vercel.app
   SENTINEL_CATALOGUE_URL=http://HOST/api/ingest  (when organizers provide)
   ```

7. Restart the backend:

   ```powershell
   Ctrl+C  # Stop current server
   uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```

8. Share the stable URL (e.g., `https://api.example.com`) with judges. The API is now reachable from Vercel.

## Deploy Dashboard to Vercel

✅ **Already deployed**: https://sentinel-gujaratvercel.app

If re-deploying or creating a new project:

1. **GitHub Repository**:
   - Push the code (never commit `.env`, `.env.local`, or tunnel tokens)
   - GitHub URL: https://github.com/snehpatel05/sentinel-gujaratvercel

2. **Vercel Project**:
   - Go to https://vercel.com/new
   - Choose **Import Git Repository**
   - Select this repository
   - Set **Root Directory** to `frontend`
Submission Verification

### Mock Mode (No Credentials)

```powershell
# Terminal 1: Backend
uvicorn app.main:app --app-dir backend --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open https://sentinel-gujaratvercel.app (deployed version) or http://localhost:5173 (local)

✅ Dashboard loads  
✅ 4 mock cameras visible on map  
✅ Alert history populated  
✅ No credentials in browser DevTools

### Live Mode (With Credentials)

1. Update `.env` with organizer-provided credentials
2. Run preflight check:

   ```powershell
   .\.venv\Scripts\python.exe backend\live_preflight.py --require-gpu
   ```

   ✅ Catalogue validated  
   ✅ Camera URLs printed  
   ✅ CUDA verified  

3. Start Cloudflare tunnel + backend
4. Open Vercel dashboard from **external device** (phone, different network)

✅ Dashboard loads  
✅ Sync cameras button works  
✅ Real camera streams appear  
✅ No credentials in browser logs
   ```
   VITE_API_URL=https://sentinel-gujaratvercel-ggt2.onrender.com
   ```

   (For live: replace with your Cloudflare tunnel URL)

   ⚠️ **Never add**: `SENTINEL_API_TOKEN`, `SENTINEL_PASSWORD`, MapTiler keys, VPN data, or any credentials.

4. **Deploy**: Vercel detects Vite config and publishes `dist/`.

5. **Update Backend CORS**:
   - Copy the Vercel URL (e.g., `https://your-project.vercel.app`)
   - Update laptop `.env`:
     ```env
     SENTINEL_CORS_ORIGINS=https://your-project.vercel.app
     ```
   - Restart backend

6. **Rebuild if needed**: Changes to `VITE_*` require Vercel redeploy (values embedded at build time).

## Pre-submission test

With the laptop, API and named tunnel all running, open the Vercel link from a different phone/mobile-data connection. Confirm dashboard loads, **Sync cameras** works, alert history displays, and no credential appears in browser DevTools/network responses.
