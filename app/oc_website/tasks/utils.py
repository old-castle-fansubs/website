from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

RELEASE_DAY = 0  # monday
RELEASE_HOUR = 18
RELEASE_TZ = "Europe/Warsaw"


def get_next_release_datetime() -> datetime:
    date = datetime.now(ZoneInfo(RELEASE_TZ))
    if date.weekday() != RELEASE_DAY or date.hour >= RELEASE_HOUR:
        # release day missed, see you next week
        date += timedelta((7 + RELEASE_DAY - date.weekday()) % 7)
    return date.replace(hour=RELEASE_HOUR, minute=0, second=0, microsecond=0)
