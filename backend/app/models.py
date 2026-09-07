from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class CameraStatus(str, Enum):
    live = "live"
    offline = "offline"
    unknown = "unknown"


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class StreamUrls(BaseModel):
    rtsp: str | None = None
    hls: str | None = None
    whep: str | None = None


class Camera(BaseModel):
    id: str
    name: str
    location: GeoPoint
    status: CameraStatus = CameraStatus.unknown
    codec: str | None = None
    width: int | None = None
    height: int | None = None
    streams: StreamUrls
    district_id: str | None = None
    updated_at: datetime


class WatchlistKind(str, Enum):
    stolen_vehicle = "stolen_vehicle"
    wanted_person = "wanted_person"
    missing_person = "missing_person"
    suspect_vehicle = "suspect_vehicle"


class WatchlistEntry(BaseModel):
    id: str
    kind: WatchlistKind
    label: str
    plate: str | None = None
    description: str
    risk_level: str = "medium"
    active: bool = True


class DetectionEvent(BaseModel):
    id: str
    camera_id: str
    entity_id: str
    entity_type: str
    plate: str | None = None
    occurred_at: datetime
    source_pts_ms: float
    confidence: float = Field(ge=0, le=1)
    location: GeoPoint
    alert_id: str | None = None


class Alert(BaseModel):
    id: str
    severity: str
    title: str
    description: str
    camera_id: str
    entity_id: str
    created_at: datetime
    acknowledged: bool = False

