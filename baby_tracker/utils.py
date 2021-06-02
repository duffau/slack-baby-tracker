from datetime import datetime, timedelta


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
