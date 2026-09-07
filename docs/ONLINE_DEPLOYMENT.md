# Online deployment: Vercel + Cloudflare Tunnel

## Architecture

The dashboard is a static Vercel site. The GPU, private Sentinel credentials and RTSP ingestion stay on the RTX laptop. A Cloudflare Tunnel makes only the HTTP API reachable to the dashboard. Do not put `SENTINEL_*` secrets in Vercel.

```text
Always-on view: Judge → https://your-project.vercel.app → cloud mock API

Scheduled live view: Judge → https://sentinel-live.vercel.app → https://api.your-domain.example → laptop:8000 → Sentinel gateway
```

The laptop must stay **on, connected to the internet, and running the API/tunnel** only whenever judges need the live dashboard. It does not need to be on after you submit an unlisted demo video or when judges use the always-on mock deployment.

## Always-on mock API

`render.yaml` deploys the backend in mock mode. Create a web service from the repository on Render, leaving `SENTINEL_CATALOGUE_URL` blank. Set `SENTINEL_CORS_ORIGINS` to the production Vercel dashboard URL. Copy its HTTPS service URL into Vercel as `VITE_API_URL`. This version demonstrates the UI, seeded watchlist, history, routes and alerts even with the laptop off.

## One-time downloads

Install these on the RTX laptop:

1. Python 3.12 (already installed) and Node.js (already installed).
2. Git for Windows: <https://git-scm.com/download/win>
3. Cloudflare Tunnel (`cloudflared`): <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/>
4. Optional but recommended: FFmpeg: <https://ffmpeg.org/download.html>
5. For live AI only, install `backend/requirements-ai.txt` after GPU/CUDA checks.

## Local first run

From `sentinel-command`:

```powershell
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Verify `http://localhost:5173` before exposing anything online.

## Publish the backend safely

### Temporary rehearsal link

Run this while the API is listening on port 8000:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

It prints a random `https://…trycloudflare.com` address. This is for rehearsal only, not the final judging URL.

### Stable judging link

Create a free Cloudflare account, add a domain you control, create a named Tunnel in the Cloudflare dashboard, and map a hostname such as `api.your-domain.com` to `http://127.0.0.1:8000`. Copy the tunnel command/token Cloudflare gives you and run it on the laptop. Do not put the tunnel token in Git.

After obtaining the stable API URL, update the laptop's root `.env`:

```env
SENTINEL_CORS_ORIGINS=https://your-project.vercel.app
```

Restart the backend.

## Deploy the dashboard to Vercel

1. Create a GitHub repository and push **everything except `.env`, `.env.local`, and tunnel files**.
2. In Vercel, choose **Add New → Project**, import the repository, and set **Root Directory** to `frontend`.
3. In Vercel Project Settings → Environment Variables, set:

   ```text
   VITE_API_URL=https://api.your-domain.com
   ```

   This value is public by design. Never add Sentinel token, password, VPN data, or MapTiler secret here.
4. Deploy. Vercel detects the included Vite configuration and publishes the `dist` folder.
5. Copy the resulting `https://your-project.vercel.app` URL. Update `SENTINEL_CORS_ORIGINS` on the laptop to this exact URL and restart the API.
6. Redeploy Vercel after changing `VITE_API_URL`; Vite embeds `VITE_*` values at build time.

## Pre-submission test

With the laptop, API and named tunnel all running, open the Vercel link from a different phone/mobile-data connection. Confirm dashboard loads, **Sync cameras** works, alert history displays, and no credential appears in browser DevTools/network responses.
