from typing import Union
import dateparser as dp
from datetime import datetime

from baby_tracker import slack
from baby_tracker import db
from baby_tracker import analyze as an
from baby_tracker.utils import format_duration, format_timestamp, timedelta_to_seconds 

from baby_tracker import SLACK_OAUTH_TOKEN, CHANNEL_ID


def _validate_duration(duration):
    if duration is not None:
        assert (
            timedelta_to_seconds(duration) > 0
        ), f"Duration must be positive. Got a duration of '{duration}' seconds."


def create_duration_record(args, create_db_record, db_conn, validate_duration=_validate_duration):
    from_time, to_time = parse_duration_args(args)
    try:
        duration = to_time - from_time
    except TypeError:
        duration = None
    validate_duration(duration)
    return create_db_record(db_conn, (from_time, to_time, duration)), duration


def make_duration_status_text(db_conn, table, latest_id=None):
    status_text = []
    if latest_id:
        latest_duration = db._get_duration_record_by_id(db_conn, table, latest_id)[3]
        status_text.append(f"Duration *{format_duration(latest_duration)}*")    
    latest_date, latest_tot_duration = an.latest_daily_total_duration(db_conn, table)
    status_text.append(f"Total duration on {latest_date.strftime('%A %d/%m')}: *{format_duration(latest_tot_duration)}*")
    return "\n".join(status_text)


def parse_duration_args(args):
    from_time = parse_timestamp(args[0])
    try:
        to_time = parse_timestamp(args[1])
    except IndexError:
        to_time = None
    return from_time, to_time

def parse_timestamp(ts: Union[str, datetime]) -> datetime:
    if not isinstance(ts, datetime):
        ts = dp.parse(ts)
    return ts


def format_duration_row(row: tuple):
    id, from_time, to_time, duration, created_at, updated_at = row
    from_time = format_timestamp(from_time, short=True)
    to_time = format_timestamp(to_time, short=True)
    duration = format_duration(duration)
    return from_time, to_time, duration


def format_merged_duration_row(row: tuple):
    id, from_time, to_time, duration, created_at, updated_at, activity = row
    from_time = format_timestamp(from_time, short=True)
    to_time = format_timestamp(to_time, short=True)
    duration = format_duration(duration)
    return from_time, to_time, duration, activity


def analyze_timeline(db_conn):
    df = an.merge_duration_tables(db_conn, tables=["feed", "sleep"])    
    plot_buffer = an.timeline_plot(df, title="Timeline of breastfeeding and sleep")
    slack.post_file("timeline.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    return slack.empty_response()

