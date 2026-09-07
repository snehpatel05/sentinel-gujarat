# Sentinel sandbox integration runbook

## Before connecting

Keep gateway credentials in `.env`, not source code. Start with one camera; the gateway gives each client its own live copy, so opening every feed before it is needed wastes capacity.

## Configure

```env
SENTINEL_CATALOGUE_URL=http://HOST/api/ingest
SENTINEL_API_TOKEN=ONLY_IF_ORGANIZERS_ISSUE_ONE
SENTINEL_USERNAME=ONLY_IF_REQUIRED
SENTINEL_PASSWORD=ONLY_IF_REQUIRED
SENTINEL_VERIFY_TLS=true
```

Never set `SENTINEL_VERIFY_TLS=false` unless organizers explicitly document a development certificate and your team has approved the risk.

## Validate safely

1. Start the backend and visit `GET /health`.
2. Call `POST /api/cameras/sync`. This is read-only; the adapter does not invoke any gateway control or publish route.
3. Confirm returned camera records include a valid id, coordinates, live state, codec/properties, and URLs.
4. Pick one live camera and start its RTSP worker using its returned `streams.rtsp` value. Do not assemble a URL from a static path.
5. Use HLS or WHEP only for on-demand operator preview.

## Incident checklist

- Force RTSP TCP, not UDP.
- Read frame timing from source PTS. Never use `CAP_PROP_FPS` or frame arrival time for speed, dwell-time, or tracking.
- Treat brief initial H.264/H.265 decoder warnings as non-fatal.
- Preserve per-camera codec, resolution, and rate; do not force one universal inference batch shape.
- Reconnect after failures with exponential backoff (2 seconds to 30 seconds cap).
- At a loop/scene cut, reset long-lived tracker/gallery state rather than assuming continuity.

## Information to provide organizer support

Camera ID, exact catalogue-returned stream URL, UTC time, application version, client-side log, and current `live` value from the catalogue.

