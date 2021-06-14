from datetime import datetime, timedelta
import dateparser as dp

def timedelta_to_seconds(timedelta):
    return timedelta.total_seconds()


def to_iso(timestamp: datetime):
    return timestamp.strftime(ISO_FORMAT)


def format_timestamp(timestamp: datetime, short=False, date_only=False):
    try:
        if short:
            return timestamp.strftime("%H:%M")
        elif date_only:
            return timestamp.strftime("%a %d/%m")
        else:
            return timestamp.strftime("%d/%m-%Y %H:%M")
    except AttributeError:
        return str(timestamp)


def format_duration(duration: timedelta):
    try:
        duration = duration.seconds
    except AttributeError:
        pass
    try:
        duration_str = ""
        days, remainder = divmod(duration, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        duration_str += f"{int(days)} days " if days > 0 else ""
        duration_str += f"{int(hours):02}:{int(minutes):02}"
        return duration_str
    except Exception:
        return str(duration)


def datetime_range(start=None, end=None):
    span = end - start
    for i in range(span.days + 1):
        yield start + timedelta(days=i)


def is_timestamp(s):
    out = dp.parse(s)
    return out is not None
