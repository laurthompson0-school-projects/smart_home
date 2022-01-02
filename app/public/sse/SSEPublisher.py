# STL
from logging import Logger
from datetime import datetime
from typing import Any, Literal
from abc import ABC, abstractmethod

# PDM
from flask import Flask
from flask_sse import sse
from typeguard import typechecked
from apscheduler.schedulers.background import BackgroundScheduler

# LOCAL
from public.constants import REAL_TIME, APP_TIME
from public.time.AppClock import AppClock

TimeType = Literal[REAL_TIME, APP_TIME]


class SSEPublisher(ABC):
    """
    An abstract base class encapsulating state and functionality for publishing
    server-sent events (SSEs) from a SSE-compatible Flask app on an interval
    of real time or app time via a background scheduler with a thread pool.

    NOTE: implementing classes should:
    - override the `sseType` attribute
    - implement the `job` method
    - override the `prepare` method (if necessary)
    """

    sseType: str = "CHANGE_ME"  # NOTE: implementing classes should override this!

    logger: Logger
    app: Flask
    clock: AppClock
    scheduler: BackgroundScheduler
    jobIntervalSeconds: float
    jobIntervalTimeType: TimeType
    jobID: int

    @typechecked
    def __init__(
        self,
        logger: Logger,
        app: Flask,
        clock: AppClock,
        scheduler: BackgroundScheduler,
        jobIntervalSeconds: float,
        jobIntervalTimeType: TimeType,
    ) -> None:
        """
        Schedules a SSE-publishing job (the `job` method) to run on an interval.

        - `logger`: `Logger` object to be used for internal logging
        - `app`: `Flask` app to be used as the server for SSEs
        - `clock`: `AppClock` to be used for keeping track of app time
        - `scheduler`: `BackgroundScheduler` to run the SSE-publishing job on an interval
        - `jobIntervalSeconds`: the SSE-publishing job interval in seconds
        - `jobIntervalTimeType`: the type of time that the job interval uses (real time or app time)
        """
        self.logger = logger
        self.app = app
        self.clock = clock
        self.scheduler = scheduler
        self.jobIntervalSeconds = jobIntervalSeconds
        self.jobIntervalTimeType = jobIntervalTimeType
        self.prepare()
        self.createJob()

    def createJob(self) -> None:
        """
        Creates or replaces the SSE-publishing job.
        """
        if hasattr(self, "jobID"):
            self.scheduler.remove_job(self.jobID)
        self.jobID = self.scheduler.add_job(
            self.job,
            trigger="interval",
            next_run_time=datetime.now(),  # Start ASAP
            seconds=self.jobIntervalSeconds / self.clock.getSpeedupFactor()
            if self.jobIntervalTimeType == APP_TIME
            else self.jobIntervalSeconds,
        ).id

    def setJobInterval(self, jobIntervalSeconds: float) -> None:
        """
        Sets the job interval (interpreted according
        to the provided job interval type).
        """
        self.jobIntervalSeconds = jobIntervalSeconds
        self.createJob()

    def refreshJobInterval(self) -> None:
        """
        If running on an app time interval, refreshes the interval based on
        the current speed of the app clock. Otherwise, does nothing.
        """
        if self.jobIntervalTimeType == APP_TIME:
            self.setJobInterval(self.jobIntervalSeconds)

    def start(self) -> None:
        """
        Starts the background scheduler if it is not already running
        and reschedules the SSE-publishing job.
        """
        self.prepare()
        if not self.scheduler.running:
            self.scheduler.start()
        self.createJob()

    def publish(self, *data: Any) -> None:
        """
        Publishes each of the given data as SSEs from the
        provided app through the provided SSE channel.
        """
        with self.app.app_context():
            for d in data:
                sse.publish(d, type=self.sseType)

    def prepare(self) -> None:
        """
        Preparares the publisher to start; called by
        the constructor and the `start` method.
        """

    @abstractmethod
    def job(self) -> None:
        """
        Uses the `publish` method to publish SSEs.
        NOTE: implementing classes should implement this method!
        """
