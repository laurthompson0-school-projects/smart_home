#!/usr/bin/env python3

# STL
import os
import logging

# PDM
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sse import sse
from typeguard import check_type
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

# LOCAL
from public.constants import *
from public.time.AppClock import AppClock
from public.time.TimePublisher import TimePublisher
from public.events.Event import UserGeneratedEvent, queryEvents, isThermostatEvent
from public.events.EventStore import EventStore
from public.events.EventPublisher import EventPublisher
from public.analysis.AnalysisPublisher import AnalysisPublisher

logging.basicConfig(
    level=logging.WARNING,
    format="[%(asctime)s] [%(filename)20s:%(lineno)-4s] [%(levelname)8s]   %(message)s",
)
LOGGER = logging.getLogger(__name__)

######################################### APP ##########################################

APP = Flask(__name__)
CORS(APP)
APP.config["REDIS_URL"] = REDIS_URL
APP.register_blueprint(sse, url_prefix="/sse")

if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    # Flask runs this script with two processes to refresh code changes,
    # but we only want these instructions to run on the main process.
    APP_CLOCK = AppClock(MIN_APP_TIME, MAX_APP_TIME, DEFAULT_SPEEDUP_FACTOR)
    BACKGROUND_SCHEDULER = BackgroundScheduler(
        executors={
            "default": ThreadPoolExecutor(20),
            "processpool": ProcessPoolExecutor(5),
        },
        job_defaults={"coalesce": True, "max_instances": 3},
    )
    EVENT_STORE = EventStore()
    EVENT_STORE.putPreGeneratedEvents(*queryEvents(LOCAL_POSTGRES_URL))
    TIME_PUBLISHER = TimePublisher(
        LOGGER,
        APP,
        APP_CLOCK,
        BACKGROUND_SCHEDULER,
        *PUBLISH_TIME_INTERVAL,
    )
    EVENT_PUBLISHER = EventPublisher(
        LOGGER,
        APP,
        APP_CLOCK,
        EVENT_STORE,
        BACKGROUND_SCHEDULER,
        *PUBLISH_EVENTS_INTERVAL,
    )
    ANALYSIS_PUBLISHER = AnalysisPublisher(
        LOGGER,
        APP,
        APP_CLOCK,
        EVENT_STORE,
        BACKGROUND_SCHEDULER,
        *PUBLISH_ANALYSIS_INTERVAL,
    )

######################################## ROUTES ########################################

SUCCESS = "Success", 200


@APP.route("/constants", methods=["GET"])
def constants():
    """
    Gets constants to be used in frontend user input components.
    """
    return jsonify(
        {
            "MIN_SPEEDUP_FACTOR": MIN_SPEEDUP_FACTOR,
            "MAX_SPEEDUP_FACTOR": MAX_SPEEDUP_FACTOR,
            "MIN_THERMOSTAT_TEMP": MIN_THERMOSTAT_TEMP,
            "MAX_THERMOSTAT_TEMP": MAX_THERMOSTAT_TEMP,
            "PUBLISH_ANALYSIS_INTERVAL": PUBLISH_ANALYSIS_INTERVAL[0],
        }
    )


@APP.route("/start")
def startSimulation():
    """
    Starts/restarts the smart home dashboard simulation by:
    - clearing user-generated events from the event store
    - starting or restarting the app clock
    - resetting and starting the SSE publishers
    """
    EVENT_STORE.clearUserGeneratedEvents()
    APP_CLOCK.start()
    TIME_PUBLISHER.start()
    EVENT_PUBLISHER.start()
    ANALYSIS_PUBLISHER.start()
    return SUCCESS


@APP.route("/speed", methods=["GET", "POST"])
def appClockSpeedupFactor():
    """
    Gets or sets the speedup factor of the app clock.
    """
    if request.method == "GET":
        return jsonify(APP_CLOCK.getSpeedupFactor())

    # Request is a POST if the below code is reached
    speedupFactor = request.json.get("speed")
    if not isinstance(speedupFactor, (int, float)):
        return "The value of `speed` should be a number", 400
    if speedupFactor < MIN_SPEEDUP_FACTOR:
        return (
            f"The value of `speed` should not be less than {MIN_SPEEDUP_FACTOR}",
            400,
        )
    if speedupFactor > MAX_SPEEDUP_FACTOR:
        return (
            f"The value of `speed` should not be greater than {MAX_SPEEDUP_FACTOR}",
            400,
        )
    APP_CLOCK.setSpeedupFactor(speedupFactor)
    EVENT_PUBLISHER.refreshJobInterval()
    ANALYSIS_PUBLISHER.refreshJobInterval()
    return SUCCESS


@APP.route("/user-generated-event", methods=["POST"])
def userGeneratedEvent():
    """
    Puts a user-generated event into the event store so that it will be
    included in the calculations of derived state and utility usage.
    """
    try:
        event: UserGeneratedEvent = request.json.get("event")
        check_type("`event`", event, UserGeneratedEvent)
    except TypeError as e:
        return f"The value of `event` is invalid... {e.args[0]}", 400

    if isThermostatEvent(event):
        if event["new_value"] < MIN_THERMOSTAT_TEMP:
            return (
                f"The thermostat temperature should not be less than {MIN_THERMOSTAT_TEMP}",
                400,
            )
        if event["new_value"] > MAX_THERMOSTAT_TEMP:
            return (
                f"The thermostat temperature should not be greater than {MAX_THERMOSTAT_TEMP}",
                400,
            )

    event["time"] = int(APP_CLOCK.time())
    EVENT_STORE.putUserGeneratedEvents(event)
    return SUCCESS


######################################### MAIN #########################################

if __name__ == "__main__":
    APP.run(host="localhost", port=4000)
