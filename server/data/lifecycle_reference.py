LIFECYCLE = {
    "rice": [
        {"phase": 1, "phase_name": "Establishment", "start_day": 0, "end_day": 14, "midpoint_day": 7, "mandi_active": False, "npk_targets": {"N": 15, "P": 20, "K": 10}, "water_target": "maintain shallow water", "visual_indicators": ["seedling emergence"]},
        {"phase": 2, "phase_name": "Tillering", "start_day": 15, "end_day": 35, "midpoint_day": 25, "mandi_active": False, "npk_targets": {"N": 40, "P": 15, "K": 10}, "water_target": "alternate wetting and drying", "visual_indicators": ["active tiller growth"]},
        {"phase": 3, "phase_name": "Panicle Initiation", "start_day": 36, "end_day": 60, "midpoint_day": 48, "mandi_active": False, "npk_targets": {"N": 20, "P": 10, "K": 10}, "water_target": "consistent moisture", "visual_indicators": ["stem thickening"]},
        {"phase": 4, "phase_name": "Flowering", "start_day": 61, "end_day": 90, "midpoint_day": 75, "mandi_active": False, "npk_targets": {"N": 10, "P": 3, "K": 8}, "water_target": "avoid stress during flowering", "visual_indicators": ["flower emergence"]},
        {"phase": 5, "phase_name": "Grain Filling", "start_day": 91, "end_day": 115, "midpoint_day": 102, "mandi_active": True, "npk_targets": {"N": 10, "P": 2, "K": 8}, "water_target": "controlled irrigation", "visual_indicators": ["grain fill visible"]},
        {"phase": 6, "phase_name": "Maturity", "start_day": 116, "end_day": 140, "midpoint_day": 128, "mandi_active": True, "npk_targets": {"N": 5, "P": 0, "K": 4}, "water_target": "dry-down", "visual_indicators": ["golden panicles"]},
    ],
    "wheat": [
        {"phase": 1, "phase_name": "Germination", "start_day": 0, "end_day": 14, "midpoint_day": 7, "mandi_active": False, "npk_targets": {"N": 20, "P": 25, "K": 10}, "water_target": "light irrigation", "visual_indicators": ["seedling emergence"]},
        {"phase": 2, "phase_name": "Tillering", "start_day": 15, "end_day": 45, "midpoint_day": 30, "mandi_active": False, "npk_targets": {"N": 35, "P": 15, "K": 8}, "water_target": "uniform moisture", "visual_indicators": ["tiller expansion"]},
        {"phase": 3, "phase_name": "Jointing / Stem Elongation", "start_day": 46, "end_day": 90, "midpoint_day": 68, "mandi_active": False, "npk_targets": {"N": 35, "P": 10, "K": 8}, "water_target": "moderate irrigation", "visual_indicators": ["node elongation"]},
        {"phase": 4, "phase_name": "Booting / Heading", "start_day": 91, "end_day": 110, "midpoint_day": 100, "mandi_active": True, "npk_targets": {"N": 15, "P": 5, "K": 6}, "water_target": "avoid moisture shock", "visual_indicators": ["spike emergence"]},
        {"phase": 5, "phase_name": "Grain Filling", "start_day": 111, "end_day": 130, "midpoint_day": 120, "mandi_active": True, "npk_targets": {"N": 10, "P": 3, "K": 5}, "water_target": "controlled irrigation", "visual_indicators": ["grain swelling"]},
        {"phase": 6, "phase_name": "Maturity", "start_day": 131, "end_day": 150, "midpoint_day": 140, "mandi_active": True, "npk_targets": {"N": 5, "P": 2, "K": 3}, "water_target": "dry-down", "visual_indicators": ["harvest-ready ears"]},
    ],
    "maize": [
        {"phase": 1, "phase_name": "Emergence", "start_day": 0, "end_day": 14, "midpoint_day": 7, "mandi_active": False, "npk_targets": {"N": 25, "P": 20, "K": 15}, "water_target": "light moisture", "visual_indicators": ["uniform stand"]},
        {"phase": 2, "phase_name": "Vegetative", "start_day": 15, "end_day": 35, "midpoint_day": 25, "mandi_active": False, "npk_targets": {"N": 45, "P": 20, "K": 20}, "water_target": "steady irrigation", "visual_indicators": ["rapid leaf growth"]},
        {"phase": 3, "phase_name": "Knee High", "start_day": 36, "end_day": 55, "midpoint_day": 45, "mandi_active": False, "npk_targets": {"N": 35, "P": 15, "K": 15}, "water_target": "avoid stress", "visual_indicators": ["stem thickening"]},
        {"phase": 4, "phase_name": "Tasseling", "start_day": 56, "end_day": 80, "midpoint_day": 68, "mandi_active": False, "npk_targets": {"N": 25, "P": 10, "K": 15}, "water_target": "critical water demand", "visual_indicators": ["tassel visible"]},
        {"phase": 5, "phase_name": "Grain Fill", "start_day": 81, "end_day": 105, "midpoint_day": 93, "mandi_active": True, "npk_targets": {"N": 15, "P": 7, "K": 12}, "water_target": "maintain moisture", "visual_indicators": ["kernel fill"]},
        {"phase": 6, "phase_name": "Maturity", "start_day": 106, "end_day": 130, "midpoint_day": 118, "mandi_active": True, "npk_targets": {"N": 5, "P": 3, "K": 8}, "water_target": "dry-down", "visual_indicators": ["dry husk"]},
    ],
}

NPK_SEASON_TOTALS = {
    "rice": {"N": 100, "P": 50, "K": 50},
    "wheat": {"N": 120, "P": 60, "K": 40},
    "maize": {"N": 150, "P": 75, "K": 85},
}

MANDI_GATE_DAYS = {
    "rice": 91,
    "wheat": 91,
    "maize": 81,
}
