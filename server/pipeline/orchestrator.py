import json
import base64
from pathlib import Path

import httpx

from server.config import (
    DEMO_CACHE_ENABLED,
    OPENROUTER_API_KEY,
    OPENROUTER_APP_NAME,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)


def _infer_scenario_id(crop: str, days_elapsed: int) -> str | None:
    crop = (crop or "").lower()
    if crop == "wheat" and days_elapsed == 83:
        return "SC-02"
    if crop == "rice" and days_elapsed == 25:
        return "SC-03"
    if crop == "rice" and days_elapsed == 95:
        return "SC-04"
    return None


def _cache_path() -> Path:
    return Path("cache") / "demo_cache.json"


def _read_cache() -> dict:
    path = _cache_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_am_prompt(stage, sensors, weather, mandi_data, confidence, next_cycle_flags, image_path):
    return json.dumps(
        {
            "task": "Generate AM advisory JSON",
            "stage": stage,
            "sensors": sensors,
            "weather": weather,
            "mandi": mandi_data,
            "confidence_ceiling": confidence.get("confidence_label"),
            "next_cycle_flags": next_cycle_flags,
            "image_path": image_path,
        }
    )


def build_pm_prompt(morning_advisory, morning_sensors, evening_sensors, outcome_diff, deviation_flags, stage):
    return json.dumps(
        {
            "task": "Generate PM diagnostic JSON",
            "morning_advisory": morning_advisory,
            "morning_sensors": morning_sensors,
            "evening_sensors": evening_sensors,
            "outcome_diff": outcome_diff,
            "deviation_flags": deviation_flags,
            "stage": stage,
        }
    )


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def _cache_lookup(cache_key: str | None) -> dict | None:
    if not cache_key:
        return None
    cache = _read_cache()
    return cache.get(cache_key)


def _build_openrouter_payload(prompt: str, image_path: str | None = None) -> dict:
    content = [{"type": "text", "text": prompt}]
    if image_path:
        file_path = Path(image_path.lstrip("/"))
        if file_path.exists():
            image_b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                }
            )

    return {
        "model": OPENROUTER_MODEL,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "Return only valid JSON with no markdown fences and no additional commentary.",
            },
            {"role": "user", "content": content},
        ],
    }


def _parse_openrouter_response(payload: dict) -> dict:
    choices = payload.get("choices") or []
    if not choices:
        return {}
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return _extract_json(content)
    if isinstance(content, list):
        joined = " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        )
        return _extract_json(joined)
    return {}


def _call_gemini(prompt: str, image_path: str | None = None) -> dict:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY missing")

    url = f"{OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": OPENROUTER_APP_NAME,
    }
    payload = _build_openrouter_payload(prompt=prompt, image_path=image_path)

    last_error = None
    for _ in range(2):
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(url, headers=headers, json=payload)

            if response.status_code in {401, 402, 403, 429, 500, 502, 503, 504}:
                raise RuntimeError(
                    f"OpenRouter unavailable or credit-limited: {response.status_code}"
                )

            response.raise_for_status()
            parsed = _parse_openrouter_response(response.json())
            if not isinstance(parsed, dict) or not parsed:
                raise RuntimeError("OpenRouter returned empty or invalid JSON payload")
            return parsed
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"OpenRouter call failed: {last_error}")


def call_gemini_am(prompt, crop: str, days_elapsed: int, image_path: str | None, mandi_active: bool):
    scenario_id = _infer_scenario_id(crop, days_elapsed)
    cache_key = f"{scenario_id}_am" if scenario_id else None

    if DEMO_CACHE_ENABLED:
        cache_hit = _cache_lookup(cache_key)
        if cache_hit is not None:
            return cache_hit
        raise RuntimeError("DEMO_CACHE_ENABLED=true and AM cache key missing")

    try:
        result = _call_gemini(prompt, image_path=image_path)
    except Exception:
        # Credits exhausted/API failure path: use cached scenario payload if available.
        fallback = _cache_lookup(cache_key)
        if fallback is not None:
            return fallback
        raise

    if not result:
        fallback = _cache_lookup(cache_key)
        if fallback is not None:
            return fallback
        raise RuntimeError("OpenRouter AM response empty")

    actions = result.get("actions") or {}
    if isinstance(actions, dict) and len(actions) > 3:
        truncated = {}
        for idx, key in enumerate(actions):
            if idx >= 3:
                break
            truncated[key] = actions[key]
        result["actions"] = truncated

    if not mandi_active:
        result["mandi_advice"] = None

    return result


def call_gemini_pm(prompt, crop: str, days_elapsed: int):
    scenario_id = _infer_scenario_id(crop, days_elapsed)
    cache_key = f"{scenario_id}_pm" if scenario_id else None

    if DEMO_CACHE_ENABLED:
        cache_hit = _cache_lookup(cache_key)
        if cache_hit is not None:
            return cache_hit
        raise RuntimeError("DEMO_CACHE_ENABLED=true and PM cache key missing")

    try:
        result = _call_gemini(prompt, image_path=None)
    except Exception:
        # Credits exhausted/API failure path: use cached scenario payload if available.
        fallback = _cache_lookup(cache_key)
        if fallback is not None:
            return fallback
        raise

    if not result:
        fallback = _cache_lookup(cache_key)
        if fallback is not None:
            return fallback
        raise RuntimeError("OpenRouter PM response empty")

    result.pop("actions", None)
    if not isinstance(result.get("next_cycle_flags"), list):
        result["next_cycle_flags"] = []
    return result
