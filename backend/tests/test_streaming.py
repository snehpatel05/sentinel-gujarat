from app.streaming import ReconnectPolicy, valid_pts_delta_ms


def test_pts_timing_never_uses_fps_or_arrival_time():
    assert valid_pts_delta_ms(None, 1000) is None
    assert valid_pts_delta_ms(1000, 1120) == 120
    assert valid_pts_delta_ms(1120, 1120) is None


def test_reconnect_is_capped():
    policy = ReconnectPolicy()
    assert 1.7 <= policy.delay(0) <= 2.3
    assert policy.delay(20) <= 34.5

