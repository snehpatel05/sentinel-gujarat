"""Validate live catalogue and local GPU prerequisites before starting workers."""
import argparse
import asyncio
import importlib.util
import sys

from app.catalogue import CatalogueError, configured_streams, fetch_catalogue
from app.config import get_settings
from app.streaming import configure_opencv_rtsp_tcp


def check_gpu() -> bool:
    if importlib.util.find_spec("torch") is None:
        print("GPU: torch is not installed")
        return False
    import torch

    available = bool(torch.cuda.is_available())
    device = torch.cuda.get_device_name(0) if available else "none"
    print(f"GPU: {'ready' if available else 'unavailable'} ({device})")
    return available


async def run(require_gpu: bool, direct_camera: str | None = None) -> int:
    settings = get_settings()
    if direct_camera:
        return await run_direct_probe(direct_camera, settings, require_gpu)
    if not settings.sentinel_catalogue_url:
        print("ERROR: Set SENTINEL_CATALOGUE_URL in .env before running live preflight.")
        return 2

    print(f"Catalogue: {settings.sentinel_catalogue_url}")
    try:
        cameras = await fetch_catalogue(settings)
    except CatalogueError as exc:
        print(f"ERROR: catalogue check failed: {exc}")
        return 1

    print(f"Cameras: {len(cameras)}")
    for camera in cameras:
        streams = camera.streams
        print(
            f"- {camera.id}: status={camera.status.value} "
            f"rtsp={'yes' if streams.rtsp else 'no'} "
            f"hls={'yes' if streams.hls else 'no'} "
            f"whep={'yes' if streams.whep else 'no'}"
        )

    gpu_ready = check_gpu()
    if require_gpu and not gpu_ready:
        print("ERROR: GPU is required for the requested live inference check.")
        return 3
    print("Live preflight passed. Start with one camera and its catalogue-provided RTSP URL.")
    return 0


async def run_direct_probe(camera_id: str, settings, require_gpu: bool) -> int:
    """Probe one credentialed RTSP feed without exposing its URL or password."""
    if not settings.sentinel_username or not settings.sentinel_password:
        print("ERROR: Set SENTINEL_USERNAME and SENTINEL_PASSWORD in .env first.")
        return 2
    if not camera_id.startswith("cam"):
        print("ERROR: Camera ID must look like cam01 through cam30.")
        return 2
    configure_opencv_rtsp_tcp()
    if importlib.util.find_spec("cv2") is None:
        print("ERROR: opencv-python is not installed.")
        return 2
    import cv2

    stream = configured_streams(camera_id, settings).rtsp
    print(f"RTSP probe: {camera_id} (TCP)")
    capture = cv2.VideoCapture(stream, cv2.CAP_FFMPEG)
    try:
        if not capture.isOpened():
            print("ERROR: RTSP connection could not be opened. Check access, camera ID, and firewall.")
            return 1
        ok, frame = capture.read()
        if not ok or frame is None:
            print("ERROR: RTSP opened but returned no frame.")
            return 1
        print(f"Frame: received ({frame.shape[1]}x{frame.shape[0]})")
    finally:
        capture.release()
    gpu_ready = check_gpu()
    if require_gpu and not gpu_ready:
        print("ERROR: GPU is required for the requested live inference check.")
        return 3
    print("Direct RTSP preflight passed. The feed is reachable and returned a frame.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Check live Sentinel API and GPU prerequisites")
    parser.add_argument("--require-gpu", action="store_true", help="fail when CUDA is unavailable")
    parser.add_argument("--probe-camera", metavar="CAMERA_ID", help="probe one direct RTSP feed, e.g. cam04")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.require_gpu, args.probe_camera)))


if __name__ == "__main__":
    main()
