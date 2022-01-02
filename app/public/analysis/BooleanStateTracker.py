# STL
from typing import Set, Dict

# PDM
from typeguard import typechecked

# LOCAL
from public.events.Event import (
    BooleanEvent,
    BooleanStateKey,
    BooleanStateType,
    StateKey,
    StateType,
)
from public.events.EventStore import EventStore
from public.analysis.Formulas import Formulas
from public.analysis.UsageRate import (
    ElectricityUsageRate,
    ELECTRICITY_USAGE_RATE_MAP,
    WaterUsageRate,
    WATER_USAGE_RATE_MAP,
)


class BooleanStateTracker:
    """
    Helper class for tracking the following basic sums across boolean-state events:
    - the total amount of time that a door or window was open
    - the total amount of time that an appliance was on
    - the total amount of electricity an appliance has used
    - the total amount of water an appliance has used
    """

    type: StateType
    key: StateKey
    value: bool
    lastTimeTrue: int
    totalTimeTrue: int
    electricityUsageRate: ElectricityUsageRate
    waterUsageRate: WaterUsageRate

    @typechecked
    def __init__(self, firstEvent: BooleanEvent) -> None:
        self.type = firstEvent["state_type"]
        self.key = firstEvent["state_key"]
        self.value = firstEvent["new_value"]
        self.lastTimeTrue = firstEvent["time"]
        self.totalTimeTrue = 0
        self.electricityUsageRate = ELECTRICITY_USAGE_RATE_MAP.get(
            self.type, ElectricityUsageRate(wattsPerSecond=0)
        )
        self.waterUsageRate = WATER_USAGE_RATE_MAP.get(
            self.type, WaterUsageRate(gallonsPerSecond=0, percentHot=0)
        )

    @typechecked
    def processEvent(self, event: BooleanEvent) -> None:
        if not event["state_key"] == self.key:
            raise ValueError(f'`event` should be a "{self.key}" event!')

        if self.value and not event["new_value"]:  # Closed or turned off
            self.totalTimeTrue += event["time"] - self.lastTimeTrue
            self.value = event["new_value"]
        elif not self.value and event["new_value"]:  # Opened or turned on
            self.lastTimeTrue = event["time"]
            self.value = event["new_value"]

    def resetTotalTimeTrue(self) -> None:
        self.totalTimeTrue = 0

    def getTotalTimeTrue(self) -> int:
        return self.totalTimeTrue

    def getTotalElectricityUsage(self) -> float:
        baseUsage = Formulas.electricityUsage(
            self.electricityUsageRate["wattsPerSecond"], self.totalTimeTrue
        )
        waterHeaterUsage = Formulas.waterHeaterElectricityUsage(
            self.waterUsageRate["gallonsPerSecond"],
            self.totalTimeTrue,
            self.waterUsageRate["percentHot"],
        )
        return baseUsage + waterHeaterUsage

    def getTotalWaterUsage(self) -> float:
        return Formulas.waterUsage(
            self.waterUsageRate["gallonsPerSecond"], self.totalTimeTrue
        )


class BooleanStateTrackerMap:
    """
    Helper class wrapping a nested mapping of `BooleanStateTracker` objects to support
    easy sum tracking for many differently-typed pieces of boolean smart home state.
    """

    eventStore: EventStore
    map: Dict[BooleanStateType, Dict[BooleanStateKey, BooleanStateTracker]]

    @typechecked
    def __init__(self, eventStore: EventStore) -> None:
        self.eventStore = eventStore
        self.map = {}

    @typechecked
    def processEvent(self, event: BooleanEvent) -> None:
        stateType, stateKey = event["state_type"], event["state_key"]
        if stateType not in self.map:
            self.map[stateType] = {}
        if stateKey not in self.map[stateType]:
            self.map[stateType][stateKey] = BooleanStateTracker(event)
        self.map[stateType][stateKey].processEvent(event)

    def clear(self) -> None:
        self.map = {}

    def resetTotalTimeTrue(self, stateTypes: Set[BooleanStateType] = None) -> None:
        """
        Resets the total time true for all tracked pieces of state with the given state types.
        If state types are not provided, all tracked pieces of state are reset.
        """
        if stateTypes:
            for stateType in stateTypes:
                for tracker in self.map.get(stateType, {}).values():
                    tracker.resetTotalTimeTrue()
        else:
            for stateType in self.map:
                for tracker in self.map[stateType].values():
                    tracker.resetTotalTimeTrue()

    def resetOpenDoorTime(self) -> None:
        """
        Resets the total time true of all tracked doors.
        """
        self.resetTotalTimeTrue({"door"})

    def resetOpenWindowTime(self) -> None:
        """
        Resets the total time true of all tracked windows.
        """
        self.resetTotalTimeTrue({"window"})

    def getTotalTimeTrue(self, stateTypes: Set[BooleanStateType] = None) -> int:
        """
        Returns the total time true of all tracked pieces of state with the given state types.
        If state types are not provided, all tracked pieces of state are included.
        """
        total = 0
        if stateTypes:
            for stateType in stateTypes:
                for tracker in self.map.get(stateType, {}).values():
                    total += tracker.getTotalTimeTrue()
        else:
            for stateType in self.map:
                for tracker in self.map[stateType].values():
                    total += tracker.getTotalTimeTrue()
        return total

    def getTotalOpenDoorTime(self) -> float:
        """
        Returns the total time true of all tracked doors.
        """
        return self.getTotalTimeTrue({"door"})

    def getTotalOpenWindowTime(self) -> float:
        """
        Returns the total time true of all tracked windows.
        """
        return self.getTotalTimeTrue({"window"})

    def getTotalElectricityUsage(self) -> float:
        """
        Returns the total electricity usage of all tracked pieces of state.
        """
        total = 0
        for stateType in self.map:
            for tracker in self.map[stateType].values():
                total += tracker.getTotalElectricityUsage()
        return total

    def getTotalWaterUsage(self) -> float:
        """
        Returns the total water usage of all tracked pieces of state.
        """
        total = 0
        for stateType in self.map:
            for tracker in self.map[stateType].values():
                total += tracker.getTotalWaterUsage()
        return total
