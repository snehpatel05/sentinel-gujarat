from app.streaming import ReconnectPolicy, configure_opencv_rtsp_tcp, valid_pts_delta_ms


def test_pts_timing_never_uses_fps_or_arrival_time():
    assert valid_pts_delta_ms(None, 1000) is None
    assert valid_pts_delta_ms(1000, 1120) == 120
    assert valid_pts_delta_ms(1120, 1120) is None


def test_reconnect_is_capped():
    policy = ReconnectPolicy()
    assert 1.7 <= policy.delay(0) <= 2.3
    assert policy.delay(20) <= 34.5


def test_opencv_capture_uses_tcp_and_bounded_connect_timeout(monkeypatch):
    monkeypatch.delenv("OPENCV_FFMPEG_CAPTURE_OPTIONS", raising=False)
    configure_opencv_rtsp_tcp()
    assert "rtsp_transport;tcp" in __import__("os").environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]
    assert "stimeout;5000000" in __import__("os").environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]

