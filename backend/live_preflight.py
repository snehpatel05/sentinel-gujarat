"""Validate live catalogue and local GPU prerequisites before starting workers."""
import argparse
import asyncio
import importlib.util
import sys

from app.catalogue import CatalogueError, fetch_catalogue
from app.config import get_settings


def check_gpu() -> bool:
    if importlib.util.find_spec("torch") is None:
        print("GPU: torch is not installed")
        return False
    import torch

    available = bool(torch.cuda.is_available())
    device = torch.cuda.get_device_name(0) if available else "none"
    print(f"GPU: {'ready' if available else 'unavailable'} ({device})")
    return available


async def run(require_gpu: bool) -> int:
    settings = get_settings()
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Check live Sentinel API and GPU prerequisites")
    parser.add_argument("--require-gpu", action="store_true", help="fail when CUDA is unavailable")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.require_gpu)))


if __name__ == "__main__":
    main()
