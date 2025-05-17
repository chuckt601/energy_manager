from zoneinfo import ZoneInfo

CAR_CHARGE_RATE_MIN = 1.44  # Kw eqivalent to 6A
CAR_CHARGE_RATE_MAX = 7.68 # Kw equivelent to 32A
HOME_BATTERY_CAPACITY = 13.6 #kh
SOC_VALUE_CONSIDERED_FULL = 91.87 #SOC value considered full
HOME_ROC_CONSIDERED_NOT_CHARGING = .02
HOME_ROC_CONSIDERED_NOT_DISCHARGING = -.02
START_OF_DAY = 8
END_OF_DAY = 19
START_OF_NIGHT = 24 
CITY = 'San Jose'
LOCAL_TZ = 'America/Los_Angeles'  # Change this to your local timezone
ELEVATION_MIN = 30 #degrees above the horizon
UPDATE_INTERVAL = 90 # in seconds
WALLBOX_USER="chucktaylorsan@gmail.com"
WALLBOX_PASSWORD="Dogs2old!"
WALLBOX_CHARGER_ID=913327
LOG_FILE = "logs/charge_log.csv"