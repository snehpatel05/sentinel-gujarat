"""Read-only adapter for the organizer-provided, dynamic camera catalogue."""
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote
import httpx
from .config import Settings
from .models import Camera, CameraStatus, GeoPoint, StreamUrls


class CatalogueError(RuntimeError):
    pass


def _first(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if source.get(key) is not None:
            return source[key]
    return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def configured_streams(camera_id: str, settings: Settings | None) -> StreamUrls:
    if settings is None:
        return StreamUrls()
    encoded_id = quote(camera_id, safe="")
    hls = f"{settings.sentinel_hls_base_url.rstrip('/')}/{encoded_id}/index.m3u8"
    whep = f"{settings.sentinel_whep_base_url.rstrip('/')}/stream/{encoded_id}/whep"
    if settings.sentinel_username and settings.sentinel_password:
        username = quote(settings.sentinel_username, safe="")
        password = quote(settings.sentinel_password, safe="")
        rtsp = f"rtsp://{username}:{password}@{settings.sentinel_rtsp_host}:{settings.sentinel_rtsp_port}{settings.sentinel_rtsp_path.rstrip('/')}/{encoded_id}"
    else:
        rtsp = f"rtsp://{settings.sentinel_rtsp_host}:{settings.sentinel_rtsp_port}{settings.sentinel_rtsp_path.rstrip('/')}/{encoded_id}"
    return StreamUrls(rtsp=rtsp, hls=hls, whep=whep)


def normalize_camera(raw: dict[str, Any], settings: Settings | None = None) -> Camera:
    """Tolerate field aliases while requiring usable identity and coordinates."""
    camera_id = _first(raw, "id", "camera_id", "cameraId")
    location = raw.get("location") or raw.get("coordinates") or {}
    lat = _as_float(_first(location, "latitude", "lat") if isinstance(location, dict) else None)
    lng = _as_float(_first(location, "longitude", "lng", "lon") if isinstance(location, dict) else None)
    if not camera_id or lat is None or lng is None:
        raise CatalogueError("Camera catalogue item is missing id or latitude/longitude")
    streams = raw.get("streams") or raw.get("urls") or {}
    if not isinstance(streams, dict):
        streams = {}
    status = str(_first(raw, "status", "live_status", "live") or "unknown").lower()
    if status in {"true", "online", "active"}:
        status = "live"
    if status in {"false", "down", "inactive"}:
        status = "offline"
    generated_streams = configured_streams(str(camera_id), settings)
    return Camera(
        id=str(camera_id), name=str(_first(raw, "name", "label", "camera_name") or camera_id),
        location=GeoPoint(latitude=lat, longitude=lng),
        status=CameraStatus(status) if status in CameraStatus._value2member_map_ else CameraStatus.unknown,
        codec=_first(raw, "codec", "video_codec"), width=_first(raw, "width"), height=_first(raw, "height"),
        district_id=_first(raw, "district_id", "districtId"),
        streams=StreamUrls(
            rtsp=_first(streams, "rtsp", "rtsp_url") or generated_streams.rtsp,
            hls=_first(streams, "hls", "hls_url") or generated_streams.hls,
            whep=_first(streams, "whep", "webrtc", "whep_url") or generated_streams.whep,
        ),
        updated_at=datetime.now(timezone.utc),
    )


async def fetch_catalogue(settings: Settings) -> list[Camera]:
    if not settings.sentinel_catalogue_url:
        return mock_catalogue()
    headers = {"Accept": "application/json"}
    if settings.sentinel_api_token:
        headers["Authorization"] = f"Bearer {settings.sentinel_api_token}"
    auth = (settings.sentinel_username, settings.sentinel_password) if settings.sentinel_username and settings.sentinel_password else None
    try:
        async with httpx.AsyncClient(timeout=20, verify=settings.sentinel_verify_tls, follow_redirects=True) as client:
            response = await client.get(settings.sentinel_catalogue_url, headers=headers, auth=auth)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "json" not in content_type:
                raise CatalogueError(
                    "The catalogue endpoint returned a sign-in page instead of JSON. "
                    "The organizer must provide an API token or documented session-auth flow."
                )
            payload = response.json()
    except CatalogueError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise CatalogueError(f"Unable to read Sentinel catalogue: {exc}") from exc
    items = payload.get("cameras", payload.get("data", payload)) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise CatalogueError("Sentinel catalogue response must contain a camera array")
    cameras, failures = [], []
    for raw in items:
        try:
            cameras.append(normalize_camera(raw, settings))
        except (CatalogueError, TypeError) as exc:
            failures.append(str(exc))
    if not cameras and failures:
        raise CatalogueError("No usable cameras returned: " + "; ".join(failures[:3]))
    return cameras


def mock_catalogue() -> list[Camera]:
    now = datetime.now(timezone.utc)
    seeds = [("AHM-001", "SG Highway Junction", 23.0505, 72.5181), ("AHM-002", "Vastrapur Lake", 23.0377, 72.5297), ("AHM-003", "IIM Crossroads", 23.0275, 72.5104), ("AHM-004", "Paldi Junction", 23.0128, 72.5620)]
    return [Camera(id=cid, name=name, location=GeoPoint(latitude=lat, longitude=lng), status=CameraStatus.live, codec="H.264", width=1920, height=1080, district_id="Ahmedabad", streams=StreamUrls(), updated_at=now) for cid, name, lat, lng in seeds]

