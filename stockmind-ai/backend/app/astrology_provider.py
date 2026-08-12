from __future__ import annotations

from datetime import datetime, timezone
import httpx

from .core import S

PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_position_rows(payload: dict | list) -> list[dict]:
    rows = payload.get("data", payload) if isinstance(payload, dict) else payload
    out = []
    for row in rows or []:
        body = (row.get("body") or row.get("planet") or "").lower()
        if not body:
            continue
        out.append({
            "body": body,
            "longitude": float(row.get("longitude", row.get("lon", 0.0))),
            "latitude": float(row.get("latitude", row.get("lat", 0.0))),
            "speed": float(row.get("speed", 0.0)),
            "retrograde": bool(row.get("retrograde", False)),
            "sign": row.get("sign", ""),
            "sign_degree": float(row.get("sign_degree", 0.0)),
        })
    return out


async def positions(dt: datetime, bodies: list[str] | None = None) -> list[dict]:
    bodies = bodies or PLANETS
    if not S.astro_base_url or not S.astro_api_key:
        raise RuntimeError("Astrology provider is not configured.")
    base = S.astro_base_url.rstrip("/")
    # Morphemeris-compatible endpoint; exact vendor mapping can be changed via env vars.
    url = f"{base}/v1/positions"
    params = {"datetime": _iso(dt), "bodies": ",".join(bodies)}
    headers = {"Authorization": f"Bearer {S.astro_api_key}"}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, params=params, headers=headers)
        r.raise_for_status()
        return normalize_position_rows(r.json())
