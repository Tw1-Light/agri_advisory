from datetime import datetime
from pathlib import Path


def validate_image(image_path, image_timestamp, sensor_timestamp, now: datetime) -> str:
    if not image_path:
        return "missing"

    normalized = image_path.lstrip("/").replace("/", "\\")
    file_path = Path(normalized)
    if not file_path.exists():
        return "missing"

    if image_timestamp is None:
        return "outdated"

    if (now - image_timestamp).total_seconds() > 86400:
        return "outdated"

    if sensor_timestamp is not None and image_timestamp > sensor_timestamp:
        return "outdated"

    return "used"
