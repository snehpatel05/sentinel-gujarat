"""Run live YOLO + ByteTrack inference on one direct Sentinel RTSP feed."""
import argparse
import re
import threading
import time
from datetime import datetime, timezone

import requests
import supervision as sv
import torch
from ultralytics import YOLO

from app.catalogue import configured_streams
from app.config import get_settings
from app.inference import FrameMetadata, RtspInferenceWorker


def main() -> None:
    parser = argparse.ArgumentParser(description="Run live Sentinel detection and tracking")
    parser.add_argument("--camera", default="cam04")
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--publish", action="store_true", help="Publish metadata to the local API")
    parser.add_argument("--latitude", type=float, help="Camera latitude required with --publish")
    parser.add_argument("--longitude", type=float, help="Camera longitude required with --publish")
    parser.add_argument("--ocr", action="store_true", help="Enable optional EasyOCR text recognition")
    args = parser.parse_args()
    if args.seconds <= 0:
        raise SystemExit("--seconds must be positive")
    if args.publish and (args.latitude is None or args.longitude is None):
        raise SystemExit("--publish requires --latitude and --longitude")

    settings = get_settings()
    stream = configured_streams(args.camera, settings).rtsp
    if not stream:
        raise SystemExit("RTSP URL could not be configured")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is unavailable")

    model = YOLO("yolo11n.pt")
    tracker = sv.ByteTrack()
    reader = None
    if args.ocr:
        import easyocr
        reader = easyocr.Reader(["en"], gpu=True, verbose=False)

    frames = 0
    tracked = 0
    published = 0
    last_published: dict[str, float] = {}
    lock = threading.Lock()

    def on_frame(frame: object, metadata: FrameMetadata) -> None:
        nonlocal frames, tracked, published
        result = model.predict(frame, device=0, verbose=False)[0]
        detections = tracker.update_with_detections(sv.Detections.from_ultralytics(result))
        labels = result.names
        plate = None
        if reader is not None:
            text = reader.readtext(frame, detail=0, paragraph=False)
            matches = [re.sub(r"[^A-Z0-9]", "", value.upper()) for value in text]
            plate = next((value for value in matches if len(value) >= 4), None)
        now = time.monotonic()
        with lock:
            frames += 1
            tracked += len(detections)
        if not args.publish:
            return
        confidences = detections.confidence if detections.confidence is not None else []
        for index, confidence in enumerate(confidences):
            track_id = detections.tracker_id[index] if detections.tracker_id is not None else None
            class_id = detections.class_id[index] if detections.class_id is not None else None
            entity_id = f"{args.camera}:{track_id if track_id is not None else index}"
            if now - last_published.get(entity_id, 0) < 2:
                continue
            payload = {
                "camera_id": args.camera,
                "entity_id": entity_id,
                "entity_type": str(labels.get(int(class_id), "object")) if class_id is not None else "object",
                "plate": plate,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "source_pts_ms": metadata.pts_ms,
                "confidence": float(confidence),
                "location": {"latitude": args.latitude, "longitude": args.longitude},
            }
            headers = {"X-Sentinel-Ingest-Token": settings.sentinel_ingest_token or ""}
            response = requests.post(f"{args.api_url.rstrip('/')}/api/events/ingest", json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            last_published[entity_id] = now
            with lock:
                published += 1

    worker = RtspInferenceWorker(args.camera, stream, on_frame, sample_fps=settings.sentinel_inference_sample_fps)
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()
    try:
        time.sleep(args.seconds)
    finally:
        worker.stop()
        thread.join(timeout=10)

    print(f"Camera: {args.camera}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Frames: {frames}")
    print(f"Tracked objects: {tracked}")
    print(f"Published events: {published}")
    if frames == 0:
        raise SystemExit("No frames reached the detector")
    print("Live detection pipeline completed.")


if __name__ == "__main__":
    main()
