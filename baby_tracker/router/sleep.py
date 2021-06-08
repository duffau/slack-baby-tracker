import dateparser as dp

from baby_tracker import db
from baby_tracker import slack
from baby_tracker import analyze as an
from baby_tracker.utils import format_timestamp, is_timestamp
from baby_tracker.router._duration import create_duration_record, make_duration_status_text, format_duration_row, format_timestamp, _validate_duration, analyze_timeline

from .config import DEFAULT_N_LIST, SLACK_OAUTH_TOKEN, CHANNEL_ID

SLEEP_HELP = """
*Examples*:
`/sl`  _This help text_
`/sl 12:30 16:45` _Register sleep between two time points_
`/sl ls 5` _List 5 latest sleep entries_
`/sl d 71` _Delete sleep record with id=71_
`/sl s 14:45` Sleep started at 14:45.
`/sl analyze` Returns plots and stats of sleeping bahaviour.
"""


def handle_sleep_request(args, db_conn):
    if args is None:
        resp = slack.response(SLEEP_HELP, response_type="ephemeral")
    elif args[0] in {"s", "start"}:
        resp = handle_sleep_start(args, db_conn)
    elif args[0] in {"e", "end"}:
        resp = handle_sleep_end(args, db_conn)
    elif args[0] in {"d", "del", "delete"}:
        resp = handle_delete_sleep(args, db_conn)
    elif args[0] in {"ls", "list"}:
        resp = handle_list_sleeps(args, db_conn)
    elif args[0] == "analyze":
        resp = handle_sleep_analyze(args, db_conn)
    elif args[0] == "status":
        resp = handle_sleep_status(args, db_conn)
    elif is_timestamp(args[0]):
        resp = handle_sleep_create(args, db_conn)
    else:
        raise ValueError("Not valid args: {args}")
    return resp


def handle_sleep_create(args, db_conn):
    sleep_id, _ = create_sleep_record(args, db_conn)
    mrk_down_message = f":sleeping: Sleep record created with Id: *{sleep_id}*.\n"
    mrk_down_message += make_duration_status_text(db_conn, "sleep", latest_id=sleep_id)
    resp = slack.response(mrk_down_message)
    return resp


def handle_sleep_start(args, db_conn):
    sleep_id, _ = create_sleep_record(args[1:], db_conn)
    id, from_time, *ignore = db.get_sleep_record_by_id(db_conn, sleep_id)
    mrk_down_message = f"Sleep record created with Id: *{sleep_id}*. Started at {format_timestamp(from_time, short=True)} :sleeping:"
    resp = slack.response(mrk_down_message)
    return resp


def handle_sleep_end(args, db_conn):
    sleep_id, from_time, to_time, *ignore = db.get_latest_sleep_record_with_null_to_time(db_conn)
    to_time = dp.parse(args[1])
    duration = to_time - from_time
    _validate_duration(duration)
    updated_sleep_record = (from_time, to_time, duration)
    db.update_sleep(db_conn, sleep_id, updated_sleep_record)
    mrk_down_message = f":sleeping: Sleep record with Id: *{sleep_id}* updated. Stopped at {format_timestamp(to_time, short=True)}."
    mrk_down_message += make_duration_status_text(db_conn, "sleep", latest_id=sleep_id)
    resp = slack.response(mrk_down_message)
    return resp


def create_sleep_record(args, db_conn):
    return create_duration_record(args, db.create_sleep, db_conn)

def handle_delete_sleep(args, db_conn):
    sleep_id = args[1]
    db.delete_sleep(db_conn, sleep_id)
    mrk_down_message = (
        f"Sleeping record with Id: *{sleep_id}* deleted :wastebasket:"
    )
    resp = slack.response(mrk_down_message)
    return resp


def handle_list_sleeps(args, db_conn):
    n = int(args[1]) if len(args) == 2 else DEFAULT_N_LIST
    rows = db.get_latest_sleep_records(db_conn, n)
    rows = [format_duration_row(row) for row in rows]
    colnames = ["from", "to", "duration"]
    table_str = slack.table(rows, colnames)
    msg_text = f"*{n} latest sleeping records:*\n{table_str}"
    return slack.response(msg_text, response_type="ephemeral")

def handle_sleep_analyze(args, db_conn):
    if args[1] in {"tot", "total"}:
        return analyze_sleep_total(db_conn)
    elif args[1] in {"avg", "average"}:
        return analyze_sleep_avg(db_conn)
    elif args[1] in {"cnt", "count"}:
        return analyze_sleep_count(db_conn)
    elif args[1] in {"tl", "timeline"}:
        return analyze_timeline(db_conn)
    else:
        raise ValueError("Not valid args: {args}")


def analyze_sleep_total(db_conn):
    df_agg_tot = an.total_duration_per_day(db_conn, "sleep")
    plot_buffer = an.duration_plot(
        df_agg_tot, 
        title="Total sleeping time each day from 06:00 to 06:00",
        scale=1/3600,
        ylabel="Duration (hours)"
    )
    slack.post_file("total_sleeping_time.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    mrk_down_message = make_duration_status_text(db_conn, "sleep")
    return slack.response(mrk_down_message, response_type="in_channel")


def analyze_sleep_avg(db_conn):
    df_agg_tot = an.avg_duration_per_day(db_conn, "sleep")
    plot_buffer = an.duration_plot(
        df_agg_tot, 
        title="Average duration of each sleep period between 06:00 to 06:00",
        scale=1/3600,
        ylabel="Duration (hours)"
    )
    slack.post_file("avg_sleeping_time.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    mrk_down_message = make_duration_status_text(db_conn, "sleep")
    return slack.response(mrk_down_message, response_type="in_channel")

def analyze_sleep_count(db_conn):
    df_agg_tot = an.count_per_day(db_conn, "sleep")
    plot_buffer = an.duration_plot(
        df_agg_tot, 
        title="Number of sleep periods between 06:00 to 06:00",
        scale=1,
        ylabel="Count"
    )
    slack.post_file("count_sleeping_time.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    mrk_down_message = make_duration_status_text(db_conn, "sleep")
    return slack.response(mrk_down_message, response_type="in_channel")


def handle_sleep_status(args, db_conn):
    mrk_down_message = make_duration_status_text(db_conn, "sleep")
    return slack.response(mrk_down_message, response_type="in_channel")
