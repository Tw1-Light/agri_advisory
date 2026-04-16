import httpx

from server.config import WEATHER_ENABLED


async def fetch_weather(lat: float, lon: float):
    if not WEATHER_ENABLED:
        return None

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": 7,
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json().get("daily", {})
            dates = payload.get("time", [])
            rain = payload.get("precipitation_sum", [])
            tmax = payload.get("temperature_2m_max", [])
            tmin = payload.get("temperature_2m_min", [])

            out = []
            for idx, item_date in enumerate(dates):
                out.append(
                    {
                        "date": item_date,
                        "rain_mm": rain[idx] if idx < len(rain) else None,
                        "temp_max": tmax[idx] if idx < len(tmax) else None,
                        "temp_min": tmin[idx] if idx < len(tmin) else None,
                    }
                )
            return out
    except Exception:
        return None
