"""
A script that generates a series of events defining the state
of the smart home over a two-month time period and saves
them as SQL insert statements in `init_schema.sql`.
"""

# STL
import random
import datetime
from typing import Literal, Union

# PDM
from meteostat import Point, Hourly


SMART_HOME_LOCATION = Point(33.5186, -86.8104)  # Birmingham, Alabama
TIME_MAP = {
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 604800,
    "month": 2592000,  # Assumes 30 days
    "Tuesday": 86400,  # Assumes 0 = midnight on Monday
    "Wednesday": 172800,
    "Thursday": 259200,
    "Friday": 345600,
    "Saturday": 432000,
    "Sunday": 518400,
}
BOOLEAN_STATE_KEYS = [
    "bedroom1OverheadLight",
    "bedroom1Lamp1",
    "bedroom1Lamp2",
    "bedroom1Window1",
    "bedroom1Window2",
    "bedroom1Tv",
    "bedroom2OverheadLight",
    "bedroom2Lamp1",
    "bedroom2Lamp2",
    "bedroom2Window1",
    "bedroom2Window2",
    "bedroom3OverheadLight",
    "bedroom3Lamp1",
    "bedroom3Lamp2",
    "bedroom3Window1",
    "bedroom3Window2",
    "bathroom1OverheadLight",
    "bathroom1ExhaustFan",
    "bathroom1Window",
    "bathroom1Faucet",
    "bathroom2OverheadLight",
    "bathroom2ExhaustFan",
    "bathroom2Window",
    "bathroom2Faucet",
    "clothesWasher",
    "clothesDryer",
    "frontDoor",
    "backDoor",
    "garageHouseDoor",
    "garageCarDoor1",
    "garageCarDoor2",
    "livingRoomOverheadLight",
    "livingRoomLamp1",
    "livingRoomLamp2",
    "livingRoomTv",
    "livingRoomWindow1",
    "livingRoomWindow2",
    "livingRoomWindow3",
    "kitchenOverheadLight",
    "kitchenStove",
    "kitchenOven",
    "kitchenMicrowave",
    "kitchenRefrigerator",
    "kitchenDishWasher",
    "kitchenWindow1",
    "kitchenWindow2",
]
LIGHT_STATE_KEYS = [
    "bedroom1OverheadLight",
    "bedroom1Lamp1",
    "bedroom1Lamp2",
    "bedroom2OverheadLight",
    "bedroom2Lamp1",
    "bedroom2Lamp2",
    "bedroom3OverheadLight",
    "bedroom3Lamp1",
    "bedroom3Lamp2",
    "bathroom1OverheadLight",
    "bathroom2OverheadLight",
    "livingRoomOverheadLight",
    "livingRoomLamp1",
    "livingRoomLamp2",
    "kitchenOverheadLight",
]
BEDROOM_BATHROOM_LIGHT_STATE_KEYS = {
    "adults": [
        "bedroom1OverheadLight",
        "bedroom1Lamp1",
        "bedroom1Lamp2",
        "bathroom1OverheadLight",
    ],
    "kids": [
        "bedroom2OverheadLight",
        "bedroom2Lamp1",
        "bedroom2Lamp2",
        "bedroom3OverheadLight",
        "bedroom3Lamp1",
        "bedroom3Lamp2",
        "bathroom2OverheadLight",
    ],
}
STATE_TYPE = {
    "outdoorTemp": "temp",
    "thermostatTemp": "temp",
    "bedroom1OverheadLight": "light",
    "bedroom1Lamp1": "light",
    "bedroom1Lamp2": "light",
    "bedroom1Window1": "window",
    "bedroom1Window2": "window",
    "bedroom1Tv": "bedroomTv",
    "bedroom2OverheadLight": "light",
    "bedroom2Lamp1": "light",
    "bedroom2Lamp2": "light",
    "bedroom2Window1": "window",
    "bedroom2Window2": "window",
    "bedroom3OverheadLight": "light",
    "bedroom3Lamp1": "light",
    "bedroom3Lamp2": "light",
    "bedroom3Window1": "window",
    "bedroom3Window2": "window",
    "bathroom1OverheadLight": "light",
    "bathroom1ExhaustFan": "bathExhaustFan",
    "bathroom1Window": "window",
    "bathroom1Faucet": ("bath", "shower"),  # Not used in script
    "bathroom2OverheadLight": "light",
    "bathroom2ExhaustFan": "bathExhaustFan",
    "bathroom2Window": "window",
    "bathroom2Faucet": ("bath", "shower"),  # Not used in script
    "clothesWasher": "clothesWasher",
    "clothesDryer": "clothesDryer",
    "frontDoor": "door",
    "backDoor": "door",
    "garageHouseDoor": "door",
    "garageCarDoor1": "door",
    "garageCarDoor2": "door",
    "livingRoomOverheadLight": "light",
    "livingRoomLamp1": "light",
    "livingRoomLamp2": "light",
    "livingRoomTv": "livingRoomTv",
    "livingRoomWindow1": "window",
    "livingRoomWindow2": "window",
    "livingRoomWindow3": "window",
    "kitchenOverheadLight": "light",
    "kitchenStove": "stove",
    "kitchenOven": "oven",
    "kitchenMicrowave": "microwave",
    "kitchenRefrigerator": "refrigerator",
    "kitchenDishWasher": "dishWasher",
    "kitchenWindow1": "window",
    "kitchenWindow2": "window",
}


def humanReadableStateKey(stateKey: str) -> str:
    parts = []
    lastSplit = 0
    for i in range(len(stateKey)):
        c = stateKey[i]
        if c.isupper() or c.isnumeric():
            parts.append(stateKey[lastSplit:i].capitalize())
            lastSplit = i
    parts.append(stateKey[lastSplit:])
    return " ".join(parts)


def booleanStateLabel(stateType: str, value: bool) -> str:
    if stateType in [
        "light",
        "bedroomTv",
        "livingRoomTv",
        "stove",
        "oven",
        "microwave",
        "refrigerator",
        "dishWasher",
        "shower",
        "bath",
        "bathExhaustFan",
        "clothesWasher",
        "clothesDryer",
    ]:
        labels = ("OFF", "ON")
    elif stateType in ["door", "window"]:
        labels = ("CLOSED", "OPEN")
    else:
        raise ValueError(f"Invalid state type: {stateType}")
    return labels[1] if value else labels[0]


def celsiusToFahrenheit(celsius: float) -> int:
    return int((9 / 5) * celsius) + 32


def isSaturdayOrSunday(day: int) -> bool:
    return (day != 0) and (
        ((day % TIME_MAP["Saturday"]) == 0) or ((day % TIME_MAP["Sunday"]) == 0)
    )


class StateGenerator:
    def __init__(self, weatherLocation, outputFilename):
        self.weatherLocation = weatherLocation
        self.outputFilename = outputFilename

        # Create new output file
        with open(outputFilename, "w") as f:
            f.write(  # Clear tables before inserting fresh set of events
                "DELETE FROM pre_generated_events.integer_event;\n"
                "DELETE FROM pre_generated_events.boolean_event;\n\n"
            )

        # Set start time to be midnight, on Monday, and at least 60 days prior
        startDate = datetime.date.today() - datetime.timedelta(days=61)
        weekday = startDate.weekday()
        startDate = startDate - datetime.timedelta(weekday)
        self.startDatetime = datetime.datetime(
            startDate.year, startDate.month, startDate.day
        )

    def generateInitialState(self) -> None:
        """Generates initial state, assuming t = 0 is a Monday at midnight"""
        for stateKey in BOOLEAN_STATE_KEYS:
            if stateKey == "kitchenRefrigerator":
                self.writeBooleanEventInsertStatement(0, stateKey, True)
            elif stateKey in ["bathroom1Faucet", "bathroom2Faucet"]:
                # Faucets are handled separately because they allow two types of events
                self.writeBooleanEventInsertStatement(0, stateKey, False, isBath=True)
                self.writeBooleanEventInsertStatement(0, stateKey, False, isShower=True)
            else:
                self.writeBooleanEventInsertStatement(0, stateKey, False)

        self.writeIntegerEventInsertStatement(0, "thermostatTemp", 70)

        weatherData = Hourly(
            self.weatherLocation, self.startDatetime, self.startDatetime
        )
        weatherData = weatherData.fetch()
        self.writeIntegerEventInsertStatement(
            0, "outdoorTemp", celsiusToFahrenheit(weatherData.temp[0])
        )

    def generateTempEvents(self) -> None:
        """Generate hourly weather data"""
        weatherData = Hourly(
            self.weatherLocation,
            self.startDatetime,
            self.startDatetime + datetime.timedelta(60),
        )
        weatherData = weatherData.fetch()
        for i in range(len(weatherData)):
            self.writeIntegerEventInsertStatement(
                i * TIME_MAP["hour"],
                "outdoorTemp",
                celsiusToFahrenheit(weatherData.temp[i]),
            )

    def generateDoorEvents(self) -> None:
        """Generate door events"""

        def doorEvent(
            t0: int,
            t1: int,
            numToInsert: int,
            garage: bool = False,
            randGarage: bool = False,
        ) -> None:
            for _ in range(numToInsert):
                if randGarage:
                    garage = random.random() < 0.2
                if garage:
                    self.writeRandomizedBooleanEventInsertStatements(
                        t0,
                        t1,
                        30,
                        random.choice(["garageCarDoor1", "garageCarDoor2"]),
                        concurrentEventStateKey="garageHouseDoor",
                    )
                else:
                    self.writeRandomizedBooleanEventInsertStatements(
                        t0, t1, 30, random.choice(["frontDoor", "backDoor"])
                    )

        # Iterate over each day
        for day in range(0, 60 * TIME_MAP["day"], TIME_MAP["day"]):
            # S-S
            if isSaturdayOrSunday(day):
                # 7a-10p: 32x 30 sec door event
                t0 = day + 7 * TIME_MAP["hour"]
                t1 = day + 22 * TIME_MAP["hour"]
                doorEvent(t0, t1, 32, randGarage=True)

            # M-F
            else:
                # 7-7:30a: 4x 30 sec door event
                morningStart = day + 7 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                morningEnd = morningStart + 30 * TIME_MAP["minute"]
                doorEvent(morningStart, morningEnd, 2)
                doorEvent(morningStart, morningEnd, 2, garage=True)

                # 3:45-4:15p: 2x 30 sec door event
                kidsStart = day + 15 * TIME_MAP["hour"] + 45 * TIME_MAP["minute"]
                kidsEnd = kidsStart + 30 * TIME_MAP["minute"]
                doorEvent(kidsStart, kidsEnd, 2)

                # 5:15-5:45p: 2x 30 sec door event
                adultsStart = day + 17 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                adultsEnd = adultsStart + 30 * TIME_MAP["minute"]
                doorEvent(adultsStart, adultsEnd, 2, garage=True)

                # 6-8p: 8x 30 sec door event
                eveningStart = day + 18 * TIME_MAP["hour"]
                eveningEnd = eveningStart + 2 * TIME_MAP["hour"]
                doorEvent(eveningStart, eveningEnd, 8, randGarage=True)

    def generateOvenStoveEvents(self) -> None:
        """Generate oven and stove events"""
        # Iterate over each day
        for day in range(0, 60 * TIME_MAP["day"], TIME_MAP["day"]):
            # S-S
            if isSaturdayOrSunday(day):
                # 5-7p: 30 min stove event
                t0 = day + 17 * TIME_MAP["hour"]
                t1 = day + 19 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 30 * TIME_MAP["minute"], "kitchenStove"
                )

                # 4-7p: 60 min oven event
                t0 = day + 16 * TIME_MAP["hour"]
                t1 = day + 19 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 60 * TIME_MAP["minute"], "kitchenOven"
                )

            # M-F
            else:
                # 5:45-7p: 15 min stove event
                t0 = day + 17 * TIME_MAP["hour"] + 45 * TIME_MAP["minute"]
                t1 = day + 19 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 15 * TIME_MAP["minute"], "kitchenStove"
                )

                # 5:45-7p: 45 min oven event
                t0 = day + 17 * TIME_MAP["hour"] + 45 * TIME_MAP["minute"]
                t1 = day + 19 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 45 * TIME_MAP["minute"], "kitchenOven"
                )

    def generateMicrowaveEvents(self) -> None:
        """Generate microwave events"""
        # Iterate over each day
        for day in range(0, 60 * TIME_MAP["day"], TIME_MAP["day"]):
            # S-S
            if isSaturdayOrSunday(day):
                # 7a-10p: 6x 5 min microwave event
                t0 = day + 7 * TIME_MAP["hour"]
                t1 = day + 22 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 5 * TIME_MAP["minute"], "kitchenMicrowave", numToInsert=6
                )

            # M-F
            else:
                # 5a-6a: 5 min microwave event
                t0 = day + 5 * TIME_MAP["hour"]
                t1 = day + 6 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 5 * TIME_MAP["minute"], "kitchenMicrowave"
                )

                # 6-7:15a: 5 min microwave event
                t0 = day + 6 * TIME_MAP["hour"]
                t1 = day + 7 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 5 * TIME_MAP["minute"], "kitchenMicrowave"
                )

                # 4:15-4:45p: 5 min microwave event
                t0 = day + 16 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                t1 = day + 16 * TIME_MAP["hour"] + 45 * TIME_MAP["minute"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 5 * TIME_MAP["minute"], "kitchenMicrowave"
                )

                # 4:45-5:15p: 5 min microwave event
                t0 = day + 16 * TIME_MAP["hour"] + 45 * TIME_MAP["minute"]
                t1 = day + 17 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 5 * TIME_MAP["minute"], "kitchenMicrowave"
                )

    def generateTvEvents(self) -> None:
        """Generate bedroom TV and living room TV events"""
        # Iterate over each day
        for day in range(0, 60 * TIME_MAP["day"], TIME_MAP["day"]):
            # S-S
            if isSaturdayOrSunday(day):
                # 7a-10p: 8hr LR TV event
                t0 = day + 7 * TIME_MAP["hour"]
                t1 = day + 22 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 8 * TIME_MAP["hour"], "livingRoomTv"
                )

                # 6a-10a: 2hr BR TV event
                t0 = day + 6 * TIME_MAP["hour"]
                t1 = day + 10 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 2 * TIME_MAP["hour"], "bedroom1Tv"
                )

            # M-F
            else:
                # 4:45-10p: 4hr LR TV event
                t0 = day + 16 * TIME_MAP["hour"] + 45 * TIME_MAP["minute"]
                t1 = day + 22 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 4 * TIME_MAP["hour"], "livingRoomTv"
                )

                # 7p-10p: 2hr BR TV event
                t0 = day + 19 * TIME_MAP["hour"]
                t1 = day + 22 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 2 * TIME_MAP["hour"], "bedroom1Tv"
                )

            # Any Day
            # 7p-10p: 2hr BR TV event
            t0 = day + 19 * TIME_MAP["hour"]
            t1 = day + 22 * TIME_MAP["hour"]
            self.writeRandomizedBooleanEventInsertStatements(
                t0, t1, 2 * TIME_MAP["hour"], "bedroom1Tv"
            )

    def generateShowerBathFanEvents(self) -> None:
        """Generate shower, bath, and bath exhaust fan events"""
        fan1 = "bathroom1ExhaustFan"
        fan2 = "bathroom2ExhaustFan"
        # Iterate over each day
        for day in range(0, 60 * TIME_MAP["day"], TIME_MAP["day"]):
            # S-S
            if isSaturdayOrSunday(day):
                # 6-7a: 15 min shower event
                t0 = day + 6 * TIME_MAP["hour"]
                t1 = day + 7 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0,
                    t1,
                    15 * TIME_MAP["minute"],
                    "bathroom1Faucet",
                    isShower=True,
                    concurrentEventStateKey=fan1,
                )

                # 7-8a: 15 min shower event
                t0 = day + 7 * TIME_MAP["hour"]
                t1 = day + 8 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0,
                    t1,
                    15 * TIME_MAP["minute"],
                    "bathroom2Faucet",
                    isShower=True,
                    concurrentEventStateKey=fan2,
                )

                # 11-12p: 15 min shower event
                t0 = day + 11 * TIME_MAP["hour"]
                t1 = day + 12 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0,
                    t1,
                    15 * TIME_MAP["minute"],
                    "bathroom1Faucet",
                    isShower=True,
                    concurrentEventStateKey=fan1,
                )

                # 12-1p: 15 min bath event
                t0 = day + 12 * TIME_MAP["hour"]
                t1 = day + 13 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0,
                    t1,
                    15 * TIME_MAP["minute"],
                    "bathroom1Faucet",
                    isBath=True,
                    concurrentEventStateKey=fan1,
                )

            # M-F
            else:
                # 5:30-6:15a: 15 min shower event
                t0 = day + 5 * TIME_MAP["hour"] + 30 * TIME_MAP["minute"]
                t1 = day + 6 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0,
                    t1,
                    15 * TIME_MAP["minute"],
                    "bathroom1Faucet",
                    isShower=True,
                    concurrentEventStateKey=fan1,
                )

                # 6:15-7a: 15 min shower event
                t0 = day + 6 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                t1 = day + 7 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0,
                    t1,
                    15 * TIME_MAP["minute"],
                    "bathroom2Faucet",
                    isShower=True,
                    concurrentEventStateKey=fan2,
                )

            # Any Day
            # 6-7p: 15 min bath event
            t0 = day + 18 * TIME_MAP["hour"]
            t1 = day + 19 * TIME_MAP["hour"]
            self.writeRandomizedBooleanEventInsertStatements(
                t0,
                t1,
                15 * TIME_MAP["minute"],
                "bathroom1Faucet",
                isBath=True,
                concurrentEventStateKey=fan1,
            )

            # 7-8p: 15 min bath event
            t0 = day + 19 * TIME_MAP["hour"]
            t1 = day + 20 * TIME_MAP["hour"]
            self.writeRandomizedBooleanEventInsertStatements(
                t0,
                t1,
                15 * TIME_MAP["minute"],
                "bathroom2Faucet",
                isBath=True,
                concurrentEventStateKey=fan2,
            )

    def generateDishwasherEvents(self) -> None:
        """Generate dishwasher events"""
        # Iterate over each week
        for week in range(0, 8 * TIME_MAP["week"], TIME_MAP["week"]):
            runDays = random.sample(range(7), 4)
            # Any 4 days, 7-10p: 45 min dishWasher event
            for day in runDays:
                t0 = week + day * TIME_MAP["day"] + 19 * TIME_MAP["hour"]
                t1 = week + day * TIME_MAP["day"] + 22 * TIME_MAP["hour"]
                self.writeRandomizedBooleanEventInsertStatements(
                    t0, t1, 45 * TIME_MAP["minute"], "kitchenDishWasher"
                )

    def generateClothesWasherDryerEvents(self) -> None:
        """Generate clothes washer and clothes dryer events"""
        dryer = "clothesDryer"
        # Iterate over each week
        for week in range(0, 8 * TIME_MAP["week"], TIME_MAP["week"]):
            runDays = random.sample(range(7), 4)
            # Any 4 days, 60 min clothes wash/dry event
            for day in runDays:
                # 7-10p on weekdays
                if day < 5:
                    t0 = week + day * TIME_MAP["day"] + 19 * TIME_MAP["hour"]
                    t1 = week + day * TIME_MAP["day"] + 22 * TIME_MAP["hour"]
                    self.writeRandomizedBooleanEventInsertStatements(
                        t0,
                        t1,
                        30 * TIME_MAP["minute"],
                        "clothesWasher",
                        concurrentEventStateKey=dryer,
                    )
                # 8a-10p on weekends
                else:
                    t0 = week + day * TIME_MAP["day"] + 8 * TIME_MAP["hour"]
                    t1 = week + day * TIME_MAP["day"] + 22 * TIME_MAP["hour"]
                    self.writeRandomizedBooleanEventInsertStatements(
                        t0,
                        t1,
                        30 * TIME_MAP["minute"],
                        "clothesWasher",
                        concurrentEventStateKey=dryer,
                    )

    def generateLightEvents(self) -> None:
        """Generate light events"""

        def randomLightChange(t0: int, t1: int) -> None:
            """Every 15 mins in a time period, all lights have 20% chance of random (ON/OFF) state change"""
            for time in range(t0, t1, 15 * TIME_MAP["minute"]):
                for stateKey in LIGHT_STATE_KEYS:
                    if random.random() < 0.2:
                        if random.random() < 0.5:
                            self.writeBooleanEventInsertStatement(time, stateKey, True)
                        else:
                            self.writeBooleanEventInsertStatement(time, stateKey, False)

        def kitchenLivingRoomLights(t0: int, t1: int, newValue: bool = True) -> None:
            """Control kitchen/living room lights"""
            for stateKey in [
                "livingRoomOverheadLight",
                "livingRoomLamp1",
                "livingRoomLamp2",
                "kitchenOverheadLight",
            ]:
                self.writeBooleanEventInsertStatement(
                    random.randint(t0, t1), stateKey, newValue
                )

        def bedroomBathroomLights(
            t0: int,
            t1: int,
            newValue: bool = True,
            include: Literal["adults", "kids", "all"] = "all",
        ) -> None:
            """Control bedroom/bathroom lights"""
            if include == "adults":
                stateKeys = BEDROOM_BATHROOM_LIGHT_STATE_KEYS["adults"]
            elif include == "kids":
                stateKeys = BEDROOM_BATHROOM_LIGHT_STATE_KEYS["kids"]
            else:
                stateKeys = (
                    BEDROOM_BATHROOM_LIGHT_STATE_KEYS["adults"]
                    + BEDROOM_BATHROOM_LIGHT_STATE_KEYS["kids"]
                )
            for stateKey in stateKeys:
                self.writeBooleanEventInsertStatement(
                    random.randint(t0, t1), stateKey, newValue
                )

        def allLightsOff(t0: int, t1: int) -> None:
            for stateKey in LIGHT_STATE_KEYS:
                self.writeBooleanEventInsertStatement(
                    random.randint(t0, t1), stateKey, False
                )

        # Iterate over each day
        for day in range(0, 60 * TIME_MAP["day"], TIME_MAP["day"]):
            # S-S
            if isSaturdayOrSunday(day):
                # 6-6:15a: bedroom lights + bathroom lights come on
                t0 = day + 6 * TIME_MAP["hour"]
                t1 = day + 6 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                bedroomBathroomLights(t0, t1)

                # 8-8:15a: kitchen/living room lights come on
                t0 = day + 8 * TIME_MAP["hour"]
                t1 = day + 8 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                kitchenLivingRoomLights(t0, t1)

                # Every 15 mins, all lights have 20% chance of state change
                t0 = day + 8 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                t1 = day + 17 * TIME_MAP["hour"]
                randomLightChange(t0, t1)

                # 5-5:30p: kitchen/living room lights all turn on if not already on
                t0 = day + 17 * TIME_MAP["hour"]
                t1 = day + 17 * TIME_MAP["hour"] + 30 * TIME_MAP["minute"]
                kitchenLivingRoomLights(t0, t1)

                # 8-8:30p: bedroom/bathroom lights all turn on if not already
                t0 = day + 20 * TIME_MAP["hour"]
                t1 = day + 20 * TIME_MAP["hour"] + 30 * TIME_MAP["minute"]
                bedroomBathroomLights(t0, t1)

                # 10-10:30p: all lights turn off
                t0 = day + 22 * TIME_MAP["hour"]
                t1 = day + 22 * TIME_MAP["hour"] + 30 * TIME_MAP["minute"]
                allLightsOff(t0, t1)

            # M-F
            else:
                # 5a-5:15a: adults wake up, bed/bath lights come on
                t0 = day + 5 * TIME_MAP["hour"]
                t1 = day + 5 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                bedroomBathroomLights(t0, t1, include="adults")

                # 5:15-5:30a: kitchen/living room lights come on, master bedroom/bathroom lights off
                t0 = day + 5 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                t1 = day + 5 * TIME_MAP["hour"] + 30 * TIME_MAP["minute"]
                kitchenLivingRoomLights(t0, t1)
                bedroomBathroomLights(t0, t1, False, "adults")

                # 6a-6:15a: kids wake up, bed/bath lights come on
                t0 = day + 6 * TIME_MAP["hour"]
                t1 = day + 6 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                bedroomBathroomLights(t0, t1, include="kids")

                # 7:15-7:30a: all lights go off
                t0 = day + 7 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                t1 = day + 7 * TIME_MAP["hour"] + 30 * TIME_MAP["minute"]
                allLightsOff(t0, t1)

                # 4:00-4:15p: kitchen/living room lights come on
                t0 = day + 16 * TIME_MAP["hour"]
                t1 = day + 16 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                kitchenLivingRoomLights(t0, t1)

                # Every 15 mins, all lights have 20% chance of state change
                t0 = day + 16 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                t1 = day + 20 * TIME_MAP["hour"]
                randomLightChange(t0, t1)

                # 8-8:15p: bedroom, bathroom lights turn on
                t0 = day + 20 * TIME_MAP["hour"]
                t1 = day + 20 * TIME_MAP["hour"] + 15 * TIME_MAP["minute"]
                bedroomBathroomLights(t0, t1)

                # 8:30-8:45p: kids lights off, living room/kitchen lights off
                t0 = day + 20 * TIME_MAP["hour"] + 30 * TIME_MAP["minute"]
                t1 = day + 20 * TIME_MAP["hour"] + 45 * TIME_MAP["minute"]
                bedroomBathroomLights(t0, t1, False, include="kids")
                kitchenLivingRoomLights(t0, t1, False)

                # 10:30p: adult bedroom/bathroom lights off
                bedroomBathroomLights(t0, t1, False, include="adults")

    def generateRefrigeratorEvents(self) -> None:
        """Generate refrigerator events"""
        # This will be empty
        pass

    def generateWindowEvents(self) -> None:
        """Generate microwave events"""
        # This will be empty
        pass

    def writeEventInsertStatement(
        self,
        table: Literal["boolean_event", "integer_event"],
        time: int,
        stateType: str,
        stateKey: str,
        newValue: Union[bool, int],
        message: str,
    ) -> None:
        """Append an SQL insert statement for the specified event to the output file"""
        assert table in ["boolean_event", "integer_event"]
        with open(self.outputFilename, "a") as f1:
            f1.write(
                f"INSERT INTO pre_generated_events.{table}\n\t"
                f"VALUES ({time}, '{stateType}', '{stateKey}', {newValue}, '{message}')\n\t"
                f"ON CONFLICT (time, state_key) DO UPDATE\n\t"
                f"SET time={time}, state_type='{stateType}', state_key='{stateKey}', new_value={newValue}, message='{message}';\n\n"
            )

    def writeIntegerEventInsertStatement(
        self, time: int, stateKey: str, newValue: int
    ) -> None:
        """Append an SQL insert statement for the specified integer event to the output file"""
        stateType = STATE_TYPE[stateKey]
        message = f"{humanReadableStateKey(stateKey)} is {newValue}"
        self.writeEventInsertStatement(
            "integer_event", time, stateType, stateKey, newValue, message
        )

    def writeBooleanEventInsertStatement(
        self,
        time: int,
        stateKey: str,
        newValue: bool,
        isBath: bool = False,
        isShower: bool = False,
    ) -> None:
        """Append an SQL insert statement for the specified boolean event to the output file"""
        assert not (isBath and isShower)
        if isBath:
            stateType = "bath"
        elif isShower:
            stateType = "shower"
        else:
            stateType = STATE_TYPE[stateKey]
        message = f"{humanReadableStateKey(stateKey)} is {booleanStateLabel(stateType, newValue)}"
        self.writeEventInsertStatement(
            "boolean_event", time, stateType, stateKey, newValue, message
        )

    def writeRandomizedBooleanEventInsertStatements(
        self,
        t0: int,
        t1: int,
        duration: int,
        stateKey: str,
        isBath: bool = False,
        isShower: bool = False,
        concurrentEventStateKey: str = None,
        numToInsert: int = 1,
    ) -> None:
        for _ in range(numToInsert):
            # Determine time of door events and insert into database
            eventStart = random.randint(t0, t1)
            eventStop = eventStart + duration

            self.writeBooleanEventInsertStatement(
                eventStart, stateKey, True, isBath, isShower
            )
            self.writeBooleanEventInsertStatement(
                eventStop, stateKey, False, isBath, isShower
            )

            # Handle things that are contingent on other things - lights/bath fans
            if concurrentEventStateKey is not None:
                # Special handler for running clothes dryer 30 mins after washer
                if concurrentEventStateKey == "clothesDryer":
                    eventStart += 30 * TIME_MAP["minute"]
                    eventStop += 30 * TIME_MAP["minute"]

                if concurrentEventStateKey == "door":
                    eventStart += 30
                    eventStop += 30

                self.writeBooleanEventInsertStatement(
                    eventStart, concurrentEventStateKey, True
                )
                self.writeBooleanEventInsertStatement(
                    eventStop, concurrentEventStateKey, False
                )

    def convertToDate(self, time: int) -> datetime.datetime:
        """Return a datetime object representing the date `time` seconds after start"""
        return self.startDatetime + datetime.timedelta(seconds=time)

    def run(self) -> None:
        self.generateTempEvents()
        self.generateInitialState()
        self.generateDoorEvents()
        self.generateOvenStoveEvents()
        self.generateTvEvents()
        self.generateShowerBathFanEvents()
        self.generateMicrowaveEvents()
        self.generateDishwasherEvents()
        self.generateClothesWasherDryerEvents()
        self.generateLightEvents()


def main() -> None:
    stateGenerator = StateGenerator(SMART_HOME_LOCATION, outputFilename="init_data.sql")
    stateGenerator.run()


if __name__ == "__main__":
    main()
