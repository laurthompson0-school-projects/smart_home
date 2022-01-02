# STL
from typing import Any, Set, Dict, Generator, Literal, Optional

# LOCAL
from public.events.Event import Event, StateKey


EventType = Literal["pre-generated", "user-generated"]
EventMap = Dict[int, Dict[StateKey, Dict[EventType, Event]]]
"""
`EventMap` is a custom map data structure that indexes events by time, state key,
and event type to support fast insertions and retrievals.

Retrieving or removing many events at once requires iterating over app time, which
results in `O(1)` time complexity because app time is bounded by constants.
"""


class EventStore:
    """
    A class wrapping an `EventMap` used for storing events during the smart home simulation.

    This class supports:
    - fast insertions, retrievals, and removals of events
    - efficiently iterating over specific groups of events
      filtered by time, state key, and event type.
    """

    map: EventMap = {}
    minTime: int
    maxTime: int

    def isEmpty(self) -> bool:
        return not bool(self.map)

    def putEvents(self, eventType: EventType, *events: Event) -> None:
        for event in events:
            time, stateKey = event["time"], event["state_key"]

            if time < getattr(self, "minTime", float("inf")):
                self.minTime = time
            if time > getattr(self, "maxTime", float("-inf")):
                self.maxTime = time

            if time not in self.map:
                self.map[time] = {}
            if stateKey not in self.map[time]:
                self.map[time][stateKey] = {}

            self.map[time][stateKey][eventType] = event

    def putPreGeneratedEvents(self, *events: Event) -> None:
        self.putEvents("pre-generated", *events)

    def putUserGeneratedEvents(self, *events: Event) -> None:
        self.putEvents("user-generated", *events)

    def clearUserGeneratedEvents(self) -> None:
        for time in range(self.minTime, self.maxTime + 1):
            if time not in self.map:
                continue
            for stateKey in list(self.map[time]):
                self.map[time][stateKey].pop("user-generated", None)

    def getEvent(self, time: int, stateKey: StateKey, eventType: EventType) -> Event:
        return self.map[time][stateKey][eventType]

    def getPreGeneratedEvent(self, time: int, stateKey: StateKey) -> Event:
        return self.getEvent(time, stateKey, "pre-generated")

    def getUserGeneratedEvent(self, time: int, stateKey: StateKey) -> Event:
        return self.getEvent(time, stateKey, "user-generated")

    def safeGetEvent(
        self, time: int, stateKey: StateKey, eventType: EventType
    ) -> Optional[Event]:
        return self.map.get(time, {}).get(stateKey, {}).get(eventType)

    def safeGetPreGeneratedEvent(
        self, time: int, stateKey: StateKey
    ) -> Optional[Event]:
        return self.safeGetEvent(time, stateKey, "pre-generated")

    def safeGetUserGeneratedEvent(
        self, time: int, stateKey: StateKey
    ) -> Optional[Event]:
        return self.safeGetEvent(time, stateKey, "user-generated")

    def yieldEvents(
        self,
        startTime: int = None,
        endTime: int = None,
        stateKeys: Set[StateKey] = None,
        eventType: EventType = None,
    ) -> Generator[Event, None, None]:
        """
        Yields events across the given timeframe that have the given state keys and event type.
        If any parameters are not provided, the associated constaints are simply ignored.
        """

        def getEventFromContainer(container: Dict[EventType, Event]) -> Optional[Event]:
            """
            If `eventType` was provided, returns the event of that type. Otherwise,
            returns either the pre-generated event or the user-generated event, with
            a preference of the user-generated event (because user-generated events take
            precedence over pre-generated events in the smart home simulation).
            """
            if eventType:
                return container.get(eventType)
            return container.get("user-generated") or container.get("pre-generated")

        if not self.map:
            return

        if startTime is None:
            startTime = self.minTime
        if endTime is None:
            endTime = self.maxTime + 1

        for time in range(startTime, endTime):
            if time not in self.map:
                continue
            if stateKeys:
                for stateKey in stateKeys:
                    if stateKey not in self.map[time]:
                        continue
                    event = getEventFromContainer(self.map[time][stateKey])
                    if event:
                        yield event
            else:
                for stateKey in self.map[time]:
                    event = getEventFromContainer(self.map[time][stateKey])
                    if event:
                        yield event

    def yieldPreGeneratedEvents(
        self,
        startTime: int = None,
        endTime: int = None,
        stateKeys: Set[StateKey] = None,
    ) -> Generator[Event, None, None]:
        return self.yieldEvents(startTime, endTime, stateKeys, "pre-generated")

    def yieldUserGeneratedEvents(
        self,
        startTime: int = None,
        endTime: int = None,
        stateKeys: Set[StateKey] = None,
    ) -> Generator[Event, None, None]:
        return self.yieldEvents(startTime, endTime, stateKeys, "user-generated")

    def getFirstEvent(self, stateKey: StateKey) -> Event:
        return next(self.yieldEvents(stateKeys={stateKey}))

    def getFirstEventValue(self, stateKey: StateKey) -> Any:
        return self.getFirstEvent(stateKey)["new_value"]
