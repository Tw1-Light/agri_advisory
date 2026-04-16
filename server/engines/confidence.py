def run_plausibility_checks(sensors: dict) -> list[str]:
    flags = []
    moisture = sensors.get("moisture")
    ph = sensors.get("ph")
    n = sensors.get("N")
    p = sensors.get("P")
    k = sensors.get("K")

    if moisture is not None and (moisture < 5 or moisture > 95):
        flags.append("moisture_outlier")
    if n == 0 and p == 0 and k == 0:
        flags.append("npk_all_zero")
    if n is not None and p is not None and k is not None and n == p == k:
        flags.append("npk_identical_values")
    if ph is not None and (ph < 4.5 or ph > 9.5):
        flags.append("ph_outlier")
    if any(v is not None and v > 900 for v in [n, p, k]):
        flags.append("npk_extreme_high")
    return flags


def compute_confidence(
    farm,
    image_status,
    weather_available,
    mandi_available,
    mandi_active,
    anomaly_count,
    sensor_age_hours,
    present_sensor_count,
) -> dict:
    raw_score = 0

    if image_status == "used":
        raw_score += 25
    elif image_status == "outdated":
        raw_score += 8

    if present_sensor_count >= 5:
        raw_score += 20
    elif present_sensor_count == 4:
        raw_score += 12
    elif present_sensor_count == 3:
        raw_score += 6

    if sensor_age_hours < 1:
        raw_score += 15
    elif sensor_age_hours <= 6:
        raw_score += 12
    elif sensor_age_hours <= 12:
        raw_score += 8
    elif sensor_age_hours <= 24:
        raw_score += 4

    if anomaly_count == 0:
        raw_score += 15
    elif anomaly_count == 1:
        raw_score += 8

    if weather_available:
        raw_score += 10

    raw_score += 10 if farm.crop.lower() in {"rice", "wheat", "maize"} else 5

    if mandi_active and mandi_available:
        raw_score += 5

    if mandi_active:
        confidence_score = int(round(raw_score))
    else:
        confidence_score = int(round((raw_score / 95.0) * 100.0))

    confidence_score = max(0, min(100, confidence_score))
    if confidence_score >= 75:
        confidence_label = "high"
    elif confidence_score >= 50:
        confidence_label = "medium"
    else:
        confidence_label = "low"

    return {"confidence_score": confidence_score, "confidence_label": confidence_label}
