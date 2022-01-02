# STL
from typing import Tuple


class Formulas:
    """
    NOTE: all time values are represented in app seconds.
    NOTE: all temperature values are represented in degrees Fahrenheit.
    NOTE: all electricity values are represented in watts.
    NOTE: all water values are represented in gallons.
    NOTE: all money values are represented in dollars.
    """

    @staticmethod
    def naturalIndoorTempChange(
        indoorTemp: float,
        outdoorTemp: float,
        totalTime: float,
        openDoorTime: float,
        openWindowTime: float,
    ) -> float:
        """
        The indoor temp changes naturally in the following (cumulative) ways:
        - For every 10 deg F difference in outdoor temp, indoor temp changes +/- 2 deg F per hour.
        - For every 10 deg F difference in outdoor temp, indoor temp changes +/- 2 deg F per 5 min of open door time.
        - For every 10 deg F difference in outdoor temp, indoor temp changes +/- 1 deg F per 5 min of open window time.
        """
        baseIndoorChangePerSecPerOutdoorDiff = 2 / (3600 * 10)  # F / s*F
        indoorChangePerOpenDoorSecPerOutdoorDiff = 2 / (60 * 5 * 10)  # F / s*F
        indoorChangePerOpenWindowSecPerOutdoorDiff = 1 / (60 * 5 * 10)  # F / s*F

        outdoorDiff = abs(outdoorTemp - indoorTemp)
        changeDirection = 1 if outdoorTemp > indoorTemp else -1
        baseChange = baseIndoorChangePerSecPerOutdoorDiff * totalTime * outdoorDiff
        openDoorChange = (
            indoorChangePerOpenDoorSecPerOutdoorDiff * openDoorTime * outdoorDiff
        )
        openWindowChange = (
            indoorChangePerOpenWindowSecPerOutdoorDiff * openWindowTime * outdoorDiff
        )
        maxPossibleChange = outdoorDiff
        unclippedChange = baseChange + openDoorChange + openWindowChange
        actualChange = min(unclippedChange, maxPossibleChange)
        return changeDirection * actualChange

    @staticmethod
    def isHvacRunning(indoorTemp: float, thermostatTemp: float) -> bool:
        """
        HVAC maintains the temp set by the thermostat within 2 deg F; if the indoor
        temp goes beyond 2 deg F of the thermostat temp, HVAC starts running.
        """
        return abs(thermostatTemp - indoorTemp) > 2

    @staticmethod
    def hvacElectricityUsage(hvacRunningTime: float) -> float:
        electricityUsageRate = 3500 / 3600  # W / s
        return electricityUsageRate * hvacRunningTime

    @staticmethod
    def hvacIndoorTempChangeAndElectricityUsage(
        indoorTemp: float,
        thermostatTemp: float,
        totalTime: float,
    ) -> Tuple[float, float]:
        """
        If HVAC is running, it changes the indoor temp by 1 deg F
        per min until it reaches the thermostat temp.
        """
        if not Formulas.isHvacRunning(indoorTemp, thermostatTemp):
            return 0, 0
        changePerSecond = 1 / 60  # F / s
        difference = abs(thermostatTemp - indoorTemp)
        changeDirection = 1 if thermostatTemp > indoorTemp else -1
        maxPossibleChange = changePerSecond * totalTime
        actualChange = min(difference, maxPossibleChange)
        hvacRunningTime = actualChange / changePerSecond
        hvacElectricityUsage = Formulas.hvacElectricityUsage(hvacRunningTime)
        return changeDirection * actualChange, hvacElectricityUsage

    @staticmethod
    def indoorTempAndHvacElectricityUsage(
        indoorTemp: float,
        outdoorTemp: float,
        thermostatTemp: float,
        totalTime: float,
        openDoorTime: float,
        openWindowTime: float,
    ) -> Tuple[float, float]:
        """
        Calculates the new indoor temp and the HVAC electricity usage since the last
        calculation based on the previous indoor temp and other variables.
        """
        naturalChange = Formulas.naturalIndoorTempChange(
            indoorTemp, outdoorTemp, totalTime, openDoorTime, openWindowTime
        )
        hvacChange, electricityUsage = Formulas.hvacIndoorTempChangeAndElectricityUsage(
            indoorTemp + naturalChange, thermostatTemp, totalTime
        )
        return indoorTemp + naturalChange + hvacChange, electricityUsage

    @staticmethod
    def usage(usageRate: float, totalTime: float) -> float:
        return usageRate * totalTime

    @staticmethod
    def electricityUsage(electricityUsageRate: float, totalTime: float) -> float:
        return Formulas.usage(electricityUsageRate, totalTime)

    @staticmethod
    def waterUsage(waterUsageRate: float, totalTime: float) -> float:
        return Formulas.usage(waterUsageRate, totalTime)

    @staticmethod
    def hotWaterUsage(
        waterUsageRate: float, totalTime: float, percentHot: float
    ) -> float:
        return Formulas.waterUsage(waterUsageRate, totalTime) * percentHot

    @staticmethod
    def waterHeaterRunningTime(waterToHeat: float) -> float:
        waterHeaterSpeed = 1 / 4 / 60  # G / s
        return waterToHeat / waterHeaterSpeed

    @staticmethod
    def waterHeaterElectricityUsage(
        waterUsageRate: float, totalTime: float, percentHot: float
    ) -> float:
        electricityUsageRate = 4500 / 3600  # W / s
        hotWaterUsage = Formulas.hotWaterUsage(waterUsageRate, totalTime, percentHot)
        runningTime = Formulas.waterHeaterRunningTime(hotWaterUsage)
        return electricityUsageRate * runningTime

    @staticmethod
    def electricityCost(electricityUsage: float, totalTime: float) -> float:
        costRate = 0.12 / 1000 / 3600  # Dollars per watt-second
        return costRate * electricityUsage * totalTime

    @staticmethod
    def waterCost(waterUsage: float) -> float:
        costRate = 2.52 / 100 / 7.48  # Dollars per gallon
        return costRate * waterUsage
