from statistics import mean


def _drop_outliers(series: list[float]) -> list[float]:
    if len(series) < 3:
        return series

    clean = [series[0]]
    for idx in range(1, len(series) - 1):
        prev_v = series[idx - 1]
        cur_v = series[idx]
        next_v = series[idx + 1]
        if cur_v > 2 * prev_v and cur_v > 2 * next_v:
            continue
        clean.append(cur_v)
    clean.append(series[-1])
    return clean


def _dedup(series: list[float]) -> list[float]:
    if not series:
        return []
    out = [series[0]]
    for value in series[1:]:
        if value != out[-1]:
            out.append(value)
    return out


def compute_trend(price_series: list[float]) -> dict:
    if not price_series:
        return {"trend": None, "delta_pct": None}

    if len(price_series) >= 1 and all(v == price_series[0] for v in price_series):
        return {"trend": "stable", "delta_pct": 0.0}

    cleaned = _dedup(_drop_outliers(price_series))
    if len(cleaned) < 4:
        return {"trend": None, "delta_pct": None}

    older_avg = mean(cleaned[:4])
    recent_avg = mean(cleaned[-3:])
    if older_avg == 0:
        return {"trend": None, "delta_pct": None}

    delta_pct = ((recent_avg - older_avg) / older_avg) * 100.0
    if delta_pct > 3:
        trend = "rising"
    elif delta_pct < -3:
        trend = "falling"
    else:
        trend = "stable"

    return {"trend": trend, "delta_pct": round(delta_pct, 2)}
