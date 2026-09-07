# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-09-07

### Added
- ✅ Mock mode with seeded cameras, alerts, and events
- ✅ Live RTSP worker scaffold with PTS-based timing
- ✅ CORS-aware React dashboard with MapLibre GIS
- ✅ Always-on deployment to Vercel + Render
- ✅ GPU support (CUDA 13.4, YOLO, EasyOCR, tracking)
- ✅ Live preflight validation command
- ✅ Sentinel catalogue adapter with resilient reconnect
- ✅ Watchlist and alert creation endpoints
- ✅ Route reconstruction for tracked entities

### Deployment
- Frontend: https://sentinel-gujarat.vercel.app (Vercel)
- Backend: https://sentinel-command-demo-api.onrender.com (Render)
- Local API: http://127.0.0.1:8000 (development)

### Documentation
- `README.md` — Project overview and quick start
- `docs/ONLINE_DEPLOYMENT.md` — Render + Vercel setup
- `docs/INTEGRATION_RUNBOOK.md` — Official catalogue integration
- `CONTRIBUTING.md` — Development guidelines
- `LICENSE` — MIT license

## Future

- [ ] Connect official Sentinel gateway when credentials arrive
- [ ] Implement YOLO + OCR detection pipeline
- [ ] Add ByteTrack for multi-object tracking
- [ ] Refine watchlist matching and re-identification
- [ ] Optimize GPU inference throughput
