import pytest
from app.catalogue import CatalogueError, configured_streams, normalize_camera
from app.config import Settings


def test_normalizes_gateway_camera_without_url_assumptions():
    camera = normalize_camera({"camera_id": "c-7", "location": {"lat": "23.03", "lon": "72.56"}, "live_status": "online", "streams": {"rtsp_url": "rtsp://example/live/variable"}})
    assert camera.id == "c-7"
    assert camera.status.value == "live"
    assert camera.streams.rtsp == "rtsp://example/live/variable"


def test_rejects_camera_without_coordinates():
    with pytest.raises(CatalogueError):
        normalize_camera({"id": "c-7", "streams": {}})


def test_builds_encoded_rtsp_url_from_camera_catalogue_id():
    settings = Settings(
        sentinel_username="alice@example.com",
        sentinel_password="private/password",
        sentinel_rtsp_host="103.250.160.189",
    )
    camera = normalize_camera({"id": "cam04", "location": {"lat": 23.03, "lon": 72.56}}, settings)
    assert camera.streams.rtsp == "rtsp://alice%40example.com:private%2Fpassword@103.250.160.189:8554/stream/cam04"
    assert camera.streams.hls == "https://cctv.corp8.cloud/cam04/index.m3u8"


def test_direct_stream_template_matches_gateway_format():
    settings = Settings(sentinel_username="alice@example.com", sentinel_password="private")
    streams = configured_streams("cam04", settings)
    assert streams.rtsp == "rtsp://alice%40example.com:private@103.250.160.189:8554/stream/cam04"
    assert streams.whep == "http://103.250.160.189:8889/stream/cam04/whep"

