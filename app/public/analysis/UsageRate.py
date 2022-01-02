# STL
from typing import TypedDict, Mapping

# LOCAL
from public.events.Event import StateType


class ElectricityUsageRate(TypedDict):
    wattsPerSecond: float


ELECTRICITY_USAGE_RATE_MAP: Mapping[StateType, ElectricityUsageRate] = {
    "light": {"wattsPerSecond": 60 / 3600},
    "bathExhaustFan": {"wattsPerSecond": 30 / 3600},
    "refrigerator": {"wattsPerSecond": 150 / 3600},
    "microwave": {"wattsPerSecond": 1100 / 3600},
    "stove": {"wattsPerSecond": 3500 / 3600},
    "oven": {"wattsPerSecond": 4000 / 3600},
    "livingRoomTv": {"wattsPerSecond": 636 / 3600},
    "bedroomTv": {"wattsPerSecond": 100 / 3600},
    "dishWasher": {"wattsPerSecond": 1800 / 3600},
    "clothesWasher": {"wattsPerSecond": 500 / 3600},
    "clothesDryer": {"wattsPerSecond": 3000 / 3600},
}


class WaterUsageRate(TypedDict):
    gallonsPerSecond: float
    percentHot: float


WATER_USAGE_RATE_MAP: Mapping[StateType, WaterUsageRate] = {
    "shower": {"gallonsPerSecond": 25 / 15 / 60, "percentHot": 0.65},
    "bath": {"gallonsPerSecond": 30 / 30 / 60, "percentHot": 0.65},
    "dishWasher": {"gallonsPerSecond": 6 / 45 / 60, "percentHot": 1},
    "clothesWasher": {"gallonsPerSecond": 20 / 30 / 60, "percentHot": 0.85},
}
