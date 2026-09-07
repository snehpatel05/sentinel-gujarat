"""Optional live edge worker.

This is intentionally separate from the web API: it keeps GPU/video load at the
edge and allows the command service to receive compact detection metadata only.
"""
from collections.abc import Callable
from dataclasses import dataclass
import logging
import time
from .streaming import ReconnectPolicy, configure_opencv_rtsp_tcp, valid_pts_delta_ms

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class FrameMetadata:
    camera_id: str
    pts_ms: float
    pts_delta_ms: float | None
    captured_monotonic: float


class RtspInferenceWorker:
    """One paced RTSP consumer; source PTS is the only motion/tracker clock.

    `on_frame` receives frames after sampling. It can run detector, OCR, ByteTrack,
    and ReID locally, then post only JSON metadata to the central service.
    """
    def __init__(self, camera_id: str, rtsp_url: str, on_frame: Callable[[object, FrameMetadata], None], sample_fps: float = 3.0, reconnect: ReconnectPolicy = ReconnectPolicy()) -> None:
        if not rtsp_url.startswith("rtsp://"):
            raise ValueError("AI inference accepts only the catalogue-provided RTSP URL")
        if sample_fps <= 0:
            raise ValueError("sample_fps must be positive")
        self.camera_id, self.rtsp_url, self.on_frame = camera_id, rtsp_url, on_frame
        self.sample_interval_ms, self.reconnect = 1000 / sample_fps, reconnect
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        configure_opencv_rtsp_tcp()
        import cv2  # lazy: dashboard can run without OpenCV installed
        attempt, previous_pts, last_processed_pts = 0, None, None
        while not self._stopped:
            capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            if not capture.isOpened():
                delay = self.reconnect.delay(attempt); attempt += 1
                log.warning("camera=%s unable to open; retry in %.1fs", self.camera_id, delay)
                time.sleep(delay); continue
            attempt = 0
            try:
                while not self._stopped:
                    ok, frame = capture.read()
                    if not ok:
                        # Mid-GOP H.264/H.265 decode warnings are normal; only an absent frame reconnects.
                        break
                    pts = float(capture.get(cv2.CAP_PROP_POS_MSEC))
                    delta = valid_pts_delta_ms(previous_pts, pts)
                    previous_pts = pts
                    if last_processed_pts is not None and pts - last_processed_pts < self.sample_interval_ms:
                        continue
                    last_processed_pts = pts
                    self.on_frame(frame, FrameMetadata(self.camera_id, pts, delta, time.monotonic()))
            finally:
                capture.release()
            if not self._stopped:
                delay = self.reconnect.delay(attempt); attempt += 1
                log.info("camera=%s disconnected; retry in %.1fs", self.camera_id, delay)
                time.sleep(delay)

