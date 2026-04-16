def _targeted_fields_from_actions(morning_actions: dict | None) -> set[str]:
    if not morning_actions:
        return set()

    text = " ".join(str(v).lower() for v in morning_actions.values())
    targeted = set()
    if "moisture" in text or "irrigat" in text or "water" in text:
        targeted.add("moisture")
    if "nitrogen" in text or " n " in f" {text} ":
        targeted.add("N")
    if "phosph" in text or " p " in f" {text} ":
        targeted.add("P")
    if "potash" in text or "potassium" in text or " k " in f" {text} ":
        targeted.add("K")
    if "ph" in text:
        targeted.add("ph")
    return targeted


def compute_outcome_diff(morning_sensors: dict, evening_sensors: dict, morning_actions: dict | None) -> dict:
    targeted = _targeted_fields_from_actions(morning_actions)
    outcome_diff = {}
    deviation_flags = []

    for field in ["moisture", "N", "P", "K", "ph"]:
        m_val = morning_sensors.get(field)
        e_val = evening_sensors.get(field)

        if m_val is None or e_val is None:
            outcome = "not_applicable"
            delta = None
        else:
            delta = e_val - m_val
            if field not in targeted:
                outcome = "not_applicable"
            elif abs(delta) <= 2:
                outcome = "no_change"
            else:
                positive_expected = field in {"moisture", "N", "P", "K"}
                if (positive_expected and delta > 2) or (not positive_expected and delta < -2):
                    outcome = "as_expected"
                else:
                    outcome = "reversed"

        outcome_diff[field] = {
            "morning": m_val,
            "evening": e_val,
            "delta": None if delta is None else round(delta, 2),
            "outcome": outcome,
        }
        if field in targeted and outcome in {"no_change", "reversed"}:
            deviation_flags.append(field)

    return {"outcome_diff": outcome_diff, "deviation_flags": deviation_flags}
