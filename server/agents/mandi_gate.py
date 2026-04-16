from datetime import datetime

import httpx

from server.config import (
    AGMARKNET_API_KEY,
    AGMARKNET_API_URL,
    AGMARKNET_ENABLED,
    MANDI_ENABLED,
)
from server.data.mandi_fixtures import MAIZE_FIXTURE, PADDY_FIXTURE
from server.engines.trend import compute_trend


def _fixture_for_crop(crop: str):
    crop_key = (crop or "").lower()
    if crop_key == "rice":
        return PADDY_FIXTURE
    if crop_key == "maize":
        return MAIZE_FIXTURE
    return None


def _build_from_fixture(crop: str):
    fixture = _fixture_for_crop(crop)
    if fixture is None:
        return None

    series = fixture["price_series"]
    trend_result = compute_trend([p["modal_price"] for p in series])
    latest = series[-1]["modal_price"] if series else None

    return {
        "commodity": fixture["commodity"],
        "mandi_name": fixture["mandi_name"],
        "price_series": series,
        "modal_price_latest": latest,
        "trend": trend_result.get("trend"),
        "delta_pct": trend_result.get("delta_pct"),
    }


def _parse_agmarknet_records(records: list[dict], fallback_commodity: str) -> dict | None:
    parsed = []
    for row in records:
        price_raw = row.get("modal_price") or row.get("modal") or row.get("price")
        date_raw = row.get("arrival_date") or row.get("date")
        try:
            price = float(str(price_raw).replace(",", "").strip())
        except Exception:
            continue

        if date_raw:
            try:
                parsed_date = datetime.strptime(str(date_raw), "%d/%m/%Y").date().isoformat()
            except Exception:
                parsed_date = str(date_raw)
        else:
            parsed_date = ""

        parsed.append({"date": parsed_date, "modal_price": price})

    if not parsed:
        return None

    parsed = parsed[-7:]
    trend_result = compute_trend([p["modal_price"] for p in parsed])
    latest = parsed[-1]["modal_price"]
    mandi_name = records[-1].get("market") or records[-1].get("mandi") or "Agmarknet"
    commodity = records[-1].get("commodity") or fallback_commodity

    return {
        "commodity": commodity,
        "mandi_name": mandi_name,
        "price_series": parsed,
        "modal_price_latest": latest,
        "trend": trend_result.get("trend"),
        "delta_pct": trend_result.get("delta_pct"),
    }


def _fetch_agmarknet(crop: str):
    if not AGMARKNET_ENABLED or not AGMARKNET_API_KEY:
        return None

    crop_key = (crop or "").lower()
    commodity_map = {
        "rice": "Paddy",
        "maize": "Maize",
        "wheat": "Wheat",
    }
    commodity = commodity_map.get(crop_key, crop_key.title())

    params = {
        "api-key": AGMARKNET_API_KEY,
        "format": "json",
        "limit": 7,
        "filters[commodity]": commodity,
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(AGMARKNET_API_URL, params=params)
        response.raise_for_status()
        payload = response.json()
        records = payload.get("records") or payload.get("result", {}).get("records") or []
        if not isinstance(records, list):
            return None
        return _parse_agmarknet_records(records, fallback_commodity=commodity)
    except Exception:
        return None


def check_mandi(stage: dict, crop: str):
    if not MANDI_ENABLED:
        return None
    if not stage.get("mandi_active"):
        return None

    live = _fetch_agmarknet(crop)
    if live is not None:
        return live

    # Demo/test fallback path on live API failure.
    return _build_from_fixture(crop)
