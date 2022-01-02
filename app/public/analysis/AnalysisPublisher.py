# STL
from logging import Logger
from typing import TypedDict, cast

# PDM
from flask import Flask
from typeguard import typechecked
from apscheduler.schedulers.background import BackgroundScheduler

# LOCAL
from public.time.AppClock import AppClock
from public.events.Event import IntegerEvent, BooleanEvent, isBooleanEvent
from public.events.EventStore import EventStore
from public.sse.SSEPublisher import SSEPublisher, TimeType
from public.analysis.Formulas import Formulas
from public.analysis.BooleanStateTracker import BooleanStateTrackerMap


class WaterUsage(TypedDict):
    gallons: float
    dollars: float


class ElectricityUsage(TypedDict):
    watts: float
    dollars: float


class UtilityUsage(TypedDict):
    water: WaterUsage
    electricity: ElectricityUsage
    totalDollars: float


class AnalysisObject(TypedDict):
    """
    Object containing the indoor temp and utility usage data
    derived from events since the last calculation,
    as well as the current app time in days.
    """

    time: float
    indoorTemp: float
    utilityUsage: UtilityUsage


class AnalysisPublisher(SSEPublisher):
    """
    An `SSEPublisher` that calculates and publishes as a SSE indoor temp and
    utility usage data based on events that occurred since the last calculation.
    """

    sseType: str = "analysis"
    lastPublishTime: int
    lastCalculationTime: int
    indoorTemp: float
    outdoorTemp: int
    thermostatTemp: int
    eventStore: EventStore
    outdoorTempStateKey: str
    thermostatTempStateKey: str
    booleanStateTrackerMap: BooleanStateTrackerMap

    # Override
    @typechecked
    def __init__(
        self,
        logger: Logger,
        app: Flask,
        clock: AppClock,
        eventStore: EventStore,
        scheduler: BackgroundScheduler,
        jobIntervalSeconds: float,
        jobIntervalType: TimeType,
    ) -> None:
        """
        Schedules a SSE-publishing job (the `job` method) to run on an interval.

        - `logger`: `Logger` object to be used for internal logging
        - `app`: `Flask` app to be used as the server for SSEs
        - `clock`: `AppClock` to be used for keeping track of app time
        - `eventStore`: `EventStore` initialized with all pre-generated events for the simulation
        - `scheduler`: `BackgroundScheduler` to run the SSE-publishing job on an interval
        - `jobIntervalSeconds`: the SSE-publishing job interval in seconds
        - `jobIntervalTimeType`: the type of time that the job interval uses (real time or app time)
        """
        if eventStore.isEmpty():
            raise ValueError("`eventStore` should contain all pre-generated events!")
        self.eventStore = eventStore
        super().__init__(
            logger, app, clock, scheduler, jobIntervalSeconds, jobIntervalType
        )

    # Override
    def prepare(self) -> None:
        self.lastPublishTime = self.lastCalculationTime = self.eventStore.minTime
        self.outdoorTemp = self.eventStore.getFirstEventValue("outdoorTemp")
        self.thermostatTemp = self.eventStore.getFirstEventValue("thermostatTemp")
        self.indoorTemp = self.thermostatTemp  # Use as initial value
        self.booleanStateTrackerMap = BooleanStateTrackerMap(self.eventStore)

    def updateIndoorTempAndReturnHvacElectricityUsage(
        self, event: IntegerEvent
    ) -> float:
        """
        Updates the indoor temp attribute with a new calculated value and returns the amount
        of electricity HVAC used to regulate indoor temp since the last calculation.

        `event` is the first event since the last calculation that
        changed either the outdoor temp or the thermostat temp.
        """
        # Save the new outdoor temp or thermostat temp
        if event["state_key"] == "outdoorTemp":
            self.outdoorTemp = event["new_value"]
        elif event["state_key"] == "thermostatTemp":
            self.thermostatTemp = event["new_value"]
        else:
            raise ValueError(
                f'`event` should be a "{"outdoorTemp"}"'
                f' or "{"thermostatTemp"}" event!'
            )
        # Calculate and save the new indoor temp
        indoorTemp, hvacElectricityUsage = Formulas.indoorTempAndHvacElectricityUsage(
            self.indoorTemp,
            self.outdoorTemp,
            self.thermostatTemp,
            event["time"] - self.lastCalculationTime,
            self.booleanStateTrackerMap.getTotalOpenDoorTime(),
            self.booleanStateTrackerMap.getTotalOpenWindowTime(),
        )
        self.indoorTemp = indoorTemp
        # Begin a new calculation timeframe
        self.lastCalculationTime = event["time"]
        self.booleanStateTrackerMap.resetOpenDoorTime()
        self.booleanStateTrackerMap.resetOpenWindowTime()
        # Return the amount of electricity HVAC used to regulate indoor temp
        return hvacElectricityUsage

    # Override
    def job(self) -> None:
        """
        Publishes an `AnalysisObject` as a SSE.
        """
        electricityUsage = 0
        self.booleanStateTrackerMap.resetTotalTimeTrue()

        start = self.lastPublishTime
        end = self.lastPublishTime = int(self.clock.time())
        for event in self.eventStore.yieldEvents(start, end):
            if isBooleanEvent(event):
                self.booleanStateTrackerMap.processEvent(cast(BooleanEvent, event))
            else:  # Integer event: outdoor temp or thermostat temp
                electricityUsage += self.updateIndoorTempAndReturnHvacElectricityUsage(
                    cast(IntegerEvent, event)
                )
        electricityUsage += self.booleanStateTrackerMap.getTotalElectricityUsage()
        electricityCost = Formulas.electricityCost(electricityUsage, end - start)

        waterUsage = self.booleanStateTrackerMap.getTotalWaterUsage()
        waterCost = Formulas.waterCost(waterUsage)

        analysisObject = AnalysisObject(
            time=self.clock.getAbsoluteSimulationTimeDays(),
            indoorTemp=self.indoorTemp,
            utilityUsage=UtilityUsage(
                electricity=ElectricityUsage(
                    watts=electricityUsage,
                    dollars=electricityCost,
                ),
                water=WaterUsage(
                    gallons=waterUsage,
                    dollars=waterCost,
                ),
                totalDollars=electricityCost + waterCost,
            ),
        )
        self.publish(analysisObject)
