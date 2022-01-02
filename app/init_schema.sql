CREATE SCHEMA IF NOT EXISTS pre_generated_events;

CREATE TYPE integer_state_type AS ENUM ('temp');
CREATE TYPE boolean_state_type AS ENUM (
    'door',
    'window',
    'light',
    'bedroomTv',
    'livingRoomTv',
    'stove',
    'oven',
    'microwave',
    'refrigerator',
    'dishWasher',
    'shower',
    'bath',
    'bathExhaustFan',
    'clothesWasher',
    'clothesDryer'
);

CREATE TYPE integer_state_key AS ENUM ('outdoorTemp', 'thermostatTemp');
CREATE TYPE boolean_state_key AS ENUM (
    'bedroom1OverheadLight',
    'bedroom1Lamp1',
    'bedroom1Lamp2',
    'bedroom1Window1',
    'bedroom1Window2',
    'bedroom1Tv',
    'bedroom2OverheadLight',
    'bedroom2Lamp1',
    'bedroom2Lamp2',
    'bedroom2Window1',
    'bedroom2Window2',
    'bedroom3OverheadLight',
    'bedroom3Lamp1',
    'bedroom3Lamp2',
    'bedroom3Window1',
    'bedroom3Window2',
    'bathroom1OverheadLight',
    'bathroom1ExhaustFan',
    'bathroom1Window',
    'bathroom1Faucet',
    'bathroom2OverheadLight',
    'bathroom2ExhaustFan',
    'bathroom2Window',
    'bathroom2Faucet',
    'clothesWasher',
    'clothesDryer',
    'frontDoor',
    'backDoor',
    'garageHouseDoor',
    'garageCarDoor1',
    'garageCarDoor2',
    'livingRoomOverheadLight',
    'livingRoomLamp1',
    'livingRoomLamp2',
    'livingRoomTv',
    'livingRoomWindow1',
    'livingRoomWindow2',
    'livingRoomWindow3',
    'kitchenOverheadLight',
    'kitchenStove',
    'kitchenOven',
    'kitchenMicrowave',
    'kitchenRefrigerator',
    'kitchenDishWasher',
    'kitchenWindow1',
    'kitchenWindow2'
);

CREATE TABLE IF NOT EXISTS pre_generated_events.integer_event (
    time integer NOT NULL,
    state_type integer_state_type NOT NULL,
    state_key integer_state_key NOT NULL,
    new_value integer NOT NULL,
    message text NOT NULL,
    PRIMARY KEY (time, state_key)
);
CREATE TABLE IF NOT EXISTS pre_generated_events.boolean_event (
    time integer NOT NULL,
    state_type boolean_state_type NOT NULL,
    state_key boolean_state_key NOT NULL,
    new_value boolean NOT NULL,
    message text NOT NULL,
    PRIMARY KEY (time, state_key)
);
