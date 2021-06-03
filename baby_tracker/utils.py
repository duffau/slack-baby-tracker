from datetime import datetime, timedelta

def timedelta_to_seconds(timedelta):
    return timedelta.total_seconds()


def to_iso(timestamp: datetime):
    return timestamp.strftime(ISO_FORMAT)


def format_timestamp(timestamp: datetime, short=False):
    try:
        if short:
            return timestamp.strftime("%H:%M")
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
        hours, remainder = divmod(duration, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}"
    except Exception:
        return str(duration)


def datetime_range(start=None, end=None):
    span = end - start
    for i in range(span.days + 1):
        yield start + timedelta(days=i)
