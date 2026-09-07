"""Stream worker primitives. This module deliberately consumes, never publishes."""
from dataclasses import dataclass
import os
import random


@dataclass(frozen=True)
class ReconnectPolicy:
    initial_seconds: float = 2.0
    maximum_seconds: float = 30.0

    def delay(self, attempt: int) -> float:
        base = min(self.maximum_seconds, self.initial_seconds * (2 ** max(0, attempt)))
        return base * random.uniform(0.85, 1.15)


def configure_opencv_rtsp_tcp() -> None:
    """Must execute before importing/initializing cv2 capture."""
    os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")


def valid_pts_delta_ms(previous_pts: float | None, current_pts: float) -> float | None:
    """Timing comes from source PTS; arrivals/FPS are intentionally never used."""
    if previous_pts is None or current_pts <= previous_pts:
        return None
    return current_pts - previous_pts

