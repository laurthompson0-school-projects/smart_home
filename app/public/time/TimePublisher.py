# PDM
from typing import TypedDict

# LOCAL
from public.sse.SSEPublisher import SSEPublisher


class TimeInfo(TypedDict):
    """
    `time` is a string representing the absolute simulation time in the following format:
    ```
    12:00:00 AM
    Monday
    Day 1
    ```

    `speed` is the current simulation speed (the current speedup factor of the app clock).
    """

    time: str
    speed: float


class TimePublisher(SSEPublisher):
    """
    An `SSEPublisher` that publishes a `TimeInfo` object as a SSE on an interval.
    """

    sseType = "time"

    # Override
    def job(self) -> None:
        """
        Publishes a `TimeInfo` object as a SSE.
        """
        timeInfo = TimeInfo(
            time=self.clock.getAbsoluteSimulationTimeString(),
            speed=self.clock.getSpeedupFactor(),
        )
        self.publish(timeInfo)
