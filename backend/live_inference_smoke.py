"""Run a bounded YOLO smoke test against one private RTSP camera feed."""
import argparse
import threading
import time

from app.catalogue import configured_streams
from app.config import get_settings
from app.inference import FrameMetadata, RtspInferenceWorker


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded GPU inference on one Sentinel camera")
    parser.add_argument("--camera", default="cam04", help="Camera ID, for example cam04")
    parser.add_argument("--seconds", type=float, default=10.0, help="How long to sample the feed")
    args = parser.parse_args()
    if args.seconds <= 0:
        raise SystemExit("--seconds must be positive")

    settings = get_settings()
    streams = configured_streams(args.camera, settings)
    if not streams.rtsp:
        raise SystemExit("RTSP URL could not be configured")

    import torch
    from ultralytics import YOLO

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is unavailable; run this on the RTX laptop or omit live inference")
    model = YOLO("yolo11n.pt")
    device = 0
    frames = 0
    detections = 0
    failures = []
    lock = threading.Lock()

    def on_frame(frame: object, metadata: FrameMetadata) -> None:
        nonlocal frames, detections
        try:
            result = model.predict(frame, device=device, verbose=False)[0]
            count = 0 if result.boxes is None else len(result.boxes)
            with lock:
                frames += 1
                detections += count
        except Exception as exc:  # Keep the worker alive while reporting smoke-test failure.
            with lock:
                failures.append(type(exc).__name__)

    worker = RtspInferenceWorker(args.camera, streams.rtsp, on_frame, sample_fps=settings.sentinel_inference_sample_fps)
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()
    try:
        time.sleep(args.seconds)
    finally:
        worker.stop()
        thread.join(timeout=10)

    print(f"Camera: {args.camera}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Sampled frames: {frames}")
    print(f"Detections: {detections}")
    if failures:
        print(f"Inference errors: {len(failures)} ({failures[0]})")
        raise SystemExit(1)
    if frames == 0:
        raise SystemExit("No frames reached the detector")
    print("Live GPU inference smoke test passed.")


if __name__ == "__main__":
    main()
