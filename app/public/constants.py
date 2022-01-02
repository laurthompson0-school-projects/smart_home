# STL
from datetime import datetime

REMOTE_POSTGRES_URL = (  # To be used in project demo
    "postgresql://Team3:Team3@138.26.48.83:5432/Team3DB"
)
LOCAL_POSTGRES_URL = (  # To be used in development
    "postgresql://username:password@localhost:5432/smart_home_simulation"
)
REDIS_URL = "redis://localhost"

REAL_TIME = "REAL_TIME"
APP_TIME = "APP_TIME"

MIN_APP_TIME = 0  # Seconds
MAX_APP_TIME = 5184000  # Seconds (60 days)

SIMULATION_START_DATE_TIMESTAMP = datetime(2021, 11, 29).timestamp()

MIN_SPEEDUP_FACTOR = 1  # 1 real second = 1 app second
MAX_SPEEDUP_FACTOR = 3600  # 1 real second = 1 app hour
DEFAULT_SPEEDUP_FACTOR = 60  # 1 real second = 1 app minute

PUBLISH_TIME_INTERVAL = (1, REAL_TIME)  # Seconds
PUBLISH_EVENTS_INTERVAL = (30, APP_TIME)  # Seconds
PUBLISH_ANALYSIS_INTERVAL = (1800, APP_TIME)  # Seconds (30 minutes)

MIN_THERMOSTAT_TEMP = 55  # Degrees Fahrenheit
MAX_THERMOSTAT_TEMP = 85  # Degrees Fahrenheit
