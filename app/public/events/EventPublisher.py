# STL
from logging import Logger

# PDM
from flask import Flask
from typeguard import typechecked
from apscheduler.schedulers.background import BackgroundScheduler

# LOCAL
from public.time.AppClock import AppClock
from public.events.EventStore import EventStore
from public.sse.SSEPublisher import SSEPublisher, TimeType


class EventPublisher(SSEPublisher):
    """
    An `SSEPublisher` that publishes unprocessed past pre-generated events
    from the provided `EventStore` as SSEs on an interval.
    """

    sseType: str = "event"
    eventStore: EventStore
    lastPublishTime: int

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
        self.lastPublishTime = self.eventStore.minTime

    # Override
    def job(self) -> None:
        """
        Publishes all unprocessed past pre-generated events from the event store as SSEs.
        """
        start = self.lastPublishTime
        end = self.lastPublishTime = int(self.clock.time())
        for event in self.eventStore.yieldPreGeneratedEvents(start, end):
            self.publish(event)
