from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .catalogue import CatalogueError, fetch_catalogue, mock_catalogue
from .config import get_settings
from .models import Alert, Camera, DetectionEvent, StreamUrls, WatchlistEntry, WatchlistKind


class State:
    cameras: dict[str, Camera] = {}
    watchlist: dict[str, WatchlistEntry] = {}
    events: list[DetectionEvent] = []
    alerts: list[Alert] = []


def seed_state() -> None:
    State.cameras = {camera.id: camera for camera in mock_catalogue()}
    wanted = WatchlistEntry(id="wl-stolen-001", kind=WatchlistKind.stolen_vehicle, label="Stolen vehicle", plate="GJ01RX4582", description="White compact SUV; investigation reference AHM-2026-014", risk_level="high")
    State.watchlist = {wanted.id: wanted}
    now = datetime.now(timezone.utc)
    route = ["AHM-001", "AHM-002", "AHM-003"]
    State.events = []
    for index, camera_id in enumerate(route):
        camera = State.cameras[camera_id]
        State.events.append(DetectionEvent(id=f"evt-seed-{index}", camera_id=camera_id, entity_id="vehicle:GJ01RX4582", entity_type="vehicle", plate="GJ01RX4582", occurred_at=now-timedelta(minutes=(2-index)*4), source_pts_ms=float(index*240000), confidence=0.94-index*.02, location=camera.location, alert_id="alert-seed-001"))
    State.alerts = [Alert(id="alert-seed-001", severity="high", title="Watchlist vehicle detected", description="GJ01RX4582 matched the seeded stolen-vehicle watchlist.", camera_id="AHM-003", entity_id="vehicle:GJ01RX4582", created_at=now, acknowledged=False)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_state()
    yield


app = FastAPI(title="Sentinel Command API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def root():
    return {
        "service": "Sentinel Command API",
        "status": "ok",
        "dashboard": "Open the Vite or Vercel dashboard URL; this tunnel exposes the API only.",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "mode": "live" if settings.live_mode else "mock", "camera_count": len(State.cameras)}


@app.get("/api/config/public")
def public_config():
    settings = get_settings()
    return {"mode": "live" if settings.live_mode else "mock", "maptilerKey": settings.sentinel_maptiler_key or ""}


@app.get("/api/cameras", response_model=list[Camera])
def cameras():
    return [_public_camera(camera) for camera in State.cameras.values()]


def _public_camera(camera: Camera) -> Camera:
    """Never send credential-bearing RTSP URLs to the browser."""
    return camera.model_copy(update={"streams": StreamUrls(hls=camera.streams.hls, whep=camera.streams.whep)})


@app.post("/api/cameras/sync", response_model=list[Camera])
async def sync_cameras():
    try:
        synced = await fetch_catalogue(get_settings())
    except CatalogueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    State.cameras = {camera.id: camera for camera in synced}
    return [_public_camera(camera) for camera in synced]


@app.get("/api/watchlist", response_model=list[WatchlistEntry])
def watchlist():
    return list(State.watchlist.values())


@app.post("/api/watchlist", response_model=WatchlistEntry, status_code=201)
def create_watchlist(entry: WatchlistEntry):
    State.watchlist[entry.id] = entry
    return entry


@app.get("/api/events", response_model=list[DetectionEvent])
def events(limit: int = 100):
    return sorted(State.events, key=lambda event: event.occurred_at, reverse=True)[:max(1, min(limit, 500))]


@app.get("/api/alerts", response_model=list[Alert])
def alerts():
    return sorted(State.alerts, key=lambda alert: alert.created_at, reverse=True)


@app.get("/api/routes/{entity_id}", response_model=list[DetectionEvent])
def route(entity_id: str):
    return sorted((event for event in State.events if event.entity_id == entity_id), key=lambda event: event.occurred_at)


@app.post("/api/demo/detect", response_model=DetectionEvent, status_code=201)
def demo_detection(camera_id: str, plate: str = "GJ01RX4582"):
    camera = State.cameras.get(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Unknown camera")
    match = next((entry for entry in State.watchlist.values() if entry.active and entry.plate == plate), None)
    alert_id = None
    entity_id = f"vehicle:{plate}"
    if match:
        alert_id = str(uuid4())
        State.alerts.append(Alert(id=alert_id, severity=match.risk_level, title="Watchlist vehicle detected", description=f"{plate} matched {match.label}.", camera_id=camera_id, entity_id=entity_id, created_at=datetime.now(timezone.utc)))
    event = DetectionEvent(id=str(uuid4()), camera_id=camera_id, entity_id=entity_id, entity_type="vehicle", plate=plate, occurred_at=datetime.now(timezone.utc), source_pts_ms=0, confidence=.95, location=camera.location, alert_id=alert_id)
    State.events.append(event)
    return event

