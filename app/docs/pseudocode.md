# Pseudocode

## Team 3

- Steven Capleton
- Landon Dyken
- Karen Horton
- Eric Latham
- Brittany Latham
- Laurence Thompson

## Pre-Generated Events

The following pseudocode describes the process for generating semi-random events based on the below [family schedule](#family-schedule) before the app runs:

```txt
generate initial state
generate outdoor temp data

define function (eventFunction) for each different type of event:
- door
- oven/stove
- microwave
- tv
- shower/bath
- dishwasher
- clothes washer/dryer
- lights

eventFunction():
    for each day:
        if weekend:
            create events based on weekend event schedule
            writeEventInsertStatements()
        if weekday:
            create events based on weekday event schedule
            writeEventInsertStatements()

writeEventInsertStatements():
    append SQL insert statements for the specified events to the output file
```

### Family Schedule

- 5:00a - adults wake up
- 6:00a - kids wake up
- 7:30a - adults/kids leave
- 4:00p - kids arrive home
- 5:30p - adults arrive home
- 8:30p - kids sleep
- 10:30p - adults sleep

#### Events M-F

- 7:15-7:45a - 4 door events
- 3:45-4:15p - 2 door events
- 5:15-5:45p - 2 door events
- 6:00-8:00p - 8 door events

<div/>

- 5:00-6:00a - 5 min microwave event
- 6:00-7:15a - 5 min microwave event
- 4:15-4:45p - 5 min microwave event
- 4:45-5:15p - 5 min microwave event

<div/>

- 5:45-7:00p - 15 min stove event
- 5:45-7:00p - 45 min oven event

<div/>

- 4:15-10:00p - 4 hour LR TV event
- 8:00-10:30p - 2 hour BR TV event

<div/>

- 5:30-6:15a - 15 min shower event
- 6:15-7:00a - 15 min shower event
- 6:00-7:00p - 15 min bath event
- 7:00-8:00p - 15 min bath event

#### Events S-S

- 7:00a-10:00p - 30 sec door event (3 times)
- 7:00a-10:00p - 5 min microwave event (6 times)
- 5:00-7:00p - 30 min stove event
- 4:00-7:00p - 60 min oven event

<div/>

- 7:00a-10:00p - 8 hour LR TV event
- 6:00-10:00a - 2 hour BR TV event
- 7:00-10:00p - 2 hour BR TV event

<div/>

- 6:00-7:00a - 15 min shower event
- 7:00-8:00a - 15 min shower event
- 11:00-12:00p - 15 min shower event
- 12:00-1:00p - 15 min bath event
- 6:00-7:00p - 15 min bath event
- 7:00-8:00p - 15 min bath event

#### Events Any Day

- 7:00-10:00p - 45 min dishwasher event (4 times/week)
- 7:00-10:00p - 60 min wash/dry event (2 times/M-F)
- 8:00a-10:00p - 60 min wash/dry event (2 times/S-S)

## Indoor Temperature & Utility Usage

The following pseudocode describes the app's process for calculating and publishing the indoor temperature and utility usage of the smart home during the simulation:

```txt
at every thirty minutes of app time:

    if previousIndoorTemp exists:
        indoorTemp = previousIndoorTemp
    else:
        indoorTemp = thermostatTemp

    electricityUsage = 0
    waterUsage = 0

    booleanStateTrackerMap = empty map for tracking total time True
                             and utility usage for boolean state

    for each event that occurred since the last calculation:

        if event is a boolean state event:

            if event changes state from True to False (closing or turning off):
                - mark booleanStateTrackerMap entry as closed/off
                - add time open/on to booleanStateTrackerMap entry

            else if event changes state from False to True (opening or turning on):
                - mark booleanStateTrackerMap entry as open/on
                - record event time in booleanStateTrackerMap

        else (event is an integer event changing outdoorTemp or thermostatTemp):

            totalOpenDoorTime = sum of door entries from booleanStateTrackerMap
            totalOpenWindowTime = sum of window entries from booleanStateTrackerMap

            - based on indoorTemp, outdoorTemp, thermostatTemp, totalOpenDoorTime,
              and totalOpenWindowTime, calculate new indoorTemp and the
              amount of electricity HVAC used to regulate indoorTemp
              since the last calculation

            - add the amount of electricity HVAC used to regulate indoorTemp
              since the last calculation to electricityUsage

            - reset door entries in booleanStateTrackerMap
            - reset window entries in booleanStateTrackerMap

    - add sum of all electricity usage from booleanStateTrackerMap to electricityUsage
    - add sum of all water usage from booleanStateTrackerMap to waterUsage

    electricityCost = cost calculated for electricityUsage
    waterCost = cost calculated for waterUsage
    totalUtilitiesCost = electricityCost + waterCost

    - publish indoorTemp, electricityUsage, electricityCost,
      waterUsage, waterCost, and totalUtilitiesCost
```
