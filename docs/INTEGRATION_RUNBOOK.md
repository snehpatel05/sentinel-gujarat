# Sentinel Gateway Integration Runbook

**Before**: Mock API with seeded cameras  
**After**: Real cameras from official Sentinel `/api/ingest` catalogue

---

## Configuration (One-Time)

Edit the root `.env` file with values **provided by organizers**:

```env
SENTINEL_CATALOGUE_URL=http://ORGANIZER_HOST/api/ingest
SENTINEL_API_TOKEN=ONLY_IF_ORGANIZERS_ISSUE_ONE
SENTINEL_USERNAME=ONLY_IF_REQUIRED
SENTINEL_PASSWORD=ONLY_IF_REQUIRED
SENTINEL_VERIFY_TLS=true
```

⚠️ **Never** commit `.env` or share it via Slack/email. Keep it on the laptop only.

---

## Tomorrow's First Command

After putting official values in root `.env`, run this from the repository root:

```powershell
.\.venv\Scripts\python.exe backend\live_preflight.py --require-gpu
```

This **validates before connecting**:

✅ Catalogue endpoint is reachable  
✅ API returns valid camera records  
✅ Stream URLs (RTSP/HLS/WHEP) are present  
✅ CUDA 13.4 is available (GPU check)  

If any check fails, the tool exits with status code 1 and prints diagnostics. No RTSP workers start until all checks pass.

---

## Safe Integration Steps

### 1. Start the Backend

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### 2. Check `/health` Endpoint

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health | Select-Object Content
```

Expected:
```json
{
  "status": "ok",
  "live_mode": true,
  "catalogue_url": "http://ORGANIZER_HOST/api/ingest"
}
```

### 3. Sync Cameras (Read-Only)

Call this endpoint to fetch and validate cameras:

```powershell
Invoke-WebRequest -Method POST http://127.0.0.1:8000/api/cameras/sync | Select-Object Content
```

**What happens**:
- API calls organizer's `/api/ingest` catalogue
- **Validates** each camera record (id + coordinates + codec required)
- **Stores** in local SQLite (data/sentinel.db)
- Returns list of loaded cameras

**Does NOT do**:
- No control commands sent to cameras
- No publish/alert endpoints called
- No credentials exposed in logs

### 4. List Loaded Cameras

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/cameras | Select-Object Content
```

Response includes real camera properties:

```json
[
  {
    "id": "CAM-001",
    "name": "Ahmedabad - Station Road",
    "status": "live",
    "codec": "h264",
    "width": 1920,
    "height": 1080,
    "streams": {
      "rtsp": "rtsp://gateway:1935/live/cam-001",
      "hls": "https://gateway/live/cam-001.m3u8",
      "whep": "https://gateway/live/cam-001?token=..."
    },
    "location": { "lat": 23.18, "lng": 72.64 },
    "updated_at": "2026-09-07T08:00:00Z"
  }
]
```

### 5. Start RTSP Inference (Optional)

For GPU processing of camera streams, the `RtspInferenceWorker` is ready to accept streams:

```python
# In development: uncomment in backend/app/main.py to spawn workers
worker = RtspInferenceWorker(
    rtsp_url=camera.streams.rtsp,
    sample_fps=3.0,
    on_frame=on_detection_callback
)
worker.run()  # Runs PTS-based frame sampling with reconnect backoff
```

---

## Incident Response

If cameras don't sync, check in order:

| Issue | Check | Fix |
|-------|-------|-----|
| Catalogue unreachable | Ping organizer host from laptop | Verify network/VPN/firewall |
| Auth required | `SENTINEL_API_TOKEN` set | Request new token from organizers |
| Invalid TLS cert | Check organizer docs | Set `SENTINEL_VERIFY_TLS=false` **only if documented** |
| Missing stream URLs | Check raw catalogue JSON | Report to organizer support |
| RTSP connection drops | Check logs for PTS errors | Exponential backoff handles this automatically |

**Information to provide organizer support**:
- Camera ID (from `/api/cameras` response)
- Exact catalogue-returned stream URL
- UTC timestamp of error
- Application version (git commit hash)
- Current camera `live` status from catalogue
- Last 20 lines of backend logs (redacted of credentials)

---

## Design Guarantees

These practices are baked into the codebase:

✅ **RTSP TCP only** — UDP never used; TCP ensures frame order  
✅ **PTS-based timing** — Never use `CAP_PROP_FPS` or frame arrival time  
✅ **Codec tolerance** — H.264/H.265 warnings at stream start are normal  
✅ **Per-camera handling** — Codec, resolution, framerate preserved per camera  
✅ **Resilient reconnect** — Exponential backoff (2s→30s) on connection loss  
✅ **Read-only catalogue** — No control, publish, or modify endpoints used  
✅ **Credentials local only** — No `SENTINEL_*` values leave the laptop  

---

## Rollback to Mock Mode

If live integration is unstable, revert to mock:

1. Edit `.env` and comment out `SENTINEL_CATALOGUE_URL`:

   ```env
   # SENTINEL_CATALOGUE_URL=http://ORGANIZER_HOST/api/ingest
   ```

2. Restart backend

3. API automatically reverts to seeded mock cameras

---

## See Also

- [ONLINE_DEPLOYMENT.md](ONLINE_DEPLOYMENT.md) — Vercel + Render + Cloudflare setup
- [Root README](../README.md) — Architecture and API overview

