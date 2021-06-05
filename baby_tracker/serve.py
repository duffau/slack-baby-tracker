import os
import traceback
from flask import Flask, request, jsonify, g
from datetime import datetime, timedelta
import dateparser as dp

from baby_tracker import db
from baby_tracker import slack
from baby_tracker import analyze as an
from baby_tracker.utils import format_duration, format_timestamp, timedelta_to_seconds 

HELP = """
This is the baby tracker.

*Examples*:
/f Register *breastfeeding*. Call command without arguments for help.
/sl Register *sleep*. Call command without arguments for help.
"""

SLEEP_HELP = """
*Examples*:
`/sl`  _This help text_
`/sl 12:30 16:45` _Register sleep between two time points_
`/sl ls 5` _List 5 latest sleep entries_
`/sl d 71` _Delete sleep record with id=71_
`/sl s 14:45` Sleep started at 14:45.
`/sl analyze` Returns plots and stats of sleeping bahaviour.
"""

FEED_HELP = """
*Examples*:
`/f`  _This help text_
`/f 12:30 16:45` _Register breastfeeding between two time points_
`/f ls 5` _List 5 latest breastfeeding entries_
`/f d 71` _Delete breastfeeding record with id=71_
`/f analyze` Returns plots and stats of breastfeeding bahaviour.
"""

WEIGHT_HELP = """
*Examples*:
`/w`  _This help text_
`/w 2021-05-18 3254` _Register weight in grams at given date_
`/w d 71` _Delete weight record with id=71_
`/w analyze` _Plot growth curves_
"""


DEFAULT_N_LIST = 5

SLACK_OAUTH_TOKEN = os.getenv("SLACK_OAUTH_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def parse_args(args_text):
    if args_text:
        return args_text.split()
    else:
        return None


app = Flask(__name__)


def get_db():
    db_conn = getattr(g, "_database", None)
    if db_conn is None:
        db_conn = g._database = db.init_db(db_file=os.getenv("DB_FILE"))
    return db_conn


@app.route("/babytracker", methods=["POST"])
def help():
    resp = help()
    return jsonify(resp)


@app.route("/babytracker/<action>", methods=["POST"])
def create(action):
    args_text = request.form.get("text")
    args = parse_args(args_text)
    db_conn = get_db()
    resp = handle_action(action, args, db_conn)
    return jsonify(resp)


def handle_action(action, args, db_conn):
    try:
        resp = _handle_action(action, args, db_conn)
    except Exception as e:
        error_message = slack.error_message(e)
        resp = slack.response(error_message, response_type="ephemeral")
        traceback_str = " ".join(traceback.format_tb(e.__traceback__))
        app.logger.error(repr(e) + "\n" + traceback_str) 
    return resp


def _handle_action(action, args, db_conn):
    if action == "feed":
        resp = handle_feed_request(args, db_conn)
    elif action == "sleep":
        resp = handle_sleep_request(args, db_conn)
    elif action == "weight":
        resp = handle_weight_request(args, db_conn)
    else:
        raise ValueError(f"action: '{action}' not recognized.")
    return resp


def help():
    resp = slack.response(HELP)
    return resp


def handle_feed_request(args, db_conn):
    if args is None:
        resp = slack.response(FEED_HELP, response_type="ephemeral")
    elif args[0] in {"s", "start"}:
        resp = handle_feed_start(args, db_conn)
    elif args[0] in {"e", "end"}:
        resp = handle_feed_end(args, db_conn)
    elif args[0] in {"d", "del", "delete"}:
        resp = handle_delete_feed(args, db_conn)
    elif args[0] in {"ls", "list"}:
        resp = handle_list_feeds(args, db_conn)
    elif args[0] == "analyze":
        resp = handle_feed_analyze(args, db_conn)
    elif args[0] == "status":
        resp = handle_feed_status(args, db_conn)
    elif is_timestamp(args[0]):
        resp = handle_feed_create(args, db_conn)
    else:
        raise ValueError("Not valid args: {args}")
    return resp

def handle_delete_feed(args, db_conn):
    feed_id = args[1]
    db.delete_feed(db_conn, feed_id)
    mrk_down_message = (
        f"Breastfeeding record with Id: *{feed_id}* deleted :wastebasket:"
    )
    resp = slack.response(mrk_down_message)
    return resp


def handle_list_feeds(args, db_conn):
    n = args[1] if len(args) == 2 else DEFAULT_N_LIST
    rows = db.get_latest_feed_records(db_conn, n)
    rows = [format_duration_row(row) for row in rows]
    colnames = ["id", "from", "to", "duration", "created_at"]
    table_str = slack.table(rows, colnames)
    msg_text = f"*{n} latest breastfeeding records:*\n{table_str}"
    return slack.response(msg_text, response_type="ephemeral")


def handle_feed_create(args, db_conn):
    feed_id, _ = create_feed_record(args, db_conn)
    mrk_down_message = f":breast-feeding: Breastfeeding record created with Id: *{feed_id}*.\n"
    mrk_down_message += make_duration_status_text(db_conn, "feed", latest_id=feed_id)
    resp = slack.response(mrk_down_message)
    return resp


def handle_feed_start(args, db_conn):
    feed_id, _ = create_feed_record(args[1:], db_conn)
    id, from_time, *ignore = db.get_feed_record_by_id(db_conn, feed_id)
    mrk_down_message = f":breast-feeding: Breastfeeding created with Id: *{feed_id}*. Started at {format_timestamp(from_time, short=True)}"
    resp = slack.response(mrk_down_message)
    return resp

def handle_feed_end(args, db_conn):
    feed_id, from_time, to_time, *ignore = db.get_latest_feed_record_with_null_to_time(db_conn)
    to_time = dp.parse(args[1])
    duration = to_time - from_time
    updated_feed_record = (from_time, to_time, duration)
    db.update_feed(db_conn, feed_id, updated_feed_record)
    mrk_down_message = f":breast-feeding: Breastfeeding record with Id: *{feed_id}* updated. Stopped at {format_timestamp(to_time, short=True)}."
    mrk_down_message += make_duration_status_text(db_conn, "feed", latest_id=feed_id)
    resp = slack.response(mrk_down_message)
    return resp

def handle_feed_analyze(args, db_conn):
    if args[1] in {"tot", "total"}:
        return analyze_feed_total(db_conn)
    elif args[1] in {"avg", "average"}:
        return analyze_feed_avg(db_conn)
    elif args[1] in {"tl", "timeline"}:
        return analyze_timeline(db_conn)
    else:
        raise ValueError("Not valid args: {args}")


def analyze_feed_total(db_conn):
    df_agg_tot = an.total_duration_per_day(db_conn, "feed")
    plot_buffer = an.duration_plot(
        df_agg_tot, 
        title="Total breastfeeding time each day from 06:00 to 06:00",
        scale=1/3600,
        ylabel="Duration (hours)"
    )
    slack.post_file("total_breatfeeding_time.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    mrk_down_message = make_duration_status_text(db_conn, "feed")
    return slack.response(mrk_down_message, response_type="in_channel")

def analyze_feed_avg(db_conn):
    df_agg_tot = an.avg_duration_per_day(db_conn, "feed")
    plot_buffer = an.duration_plot(
        df_agg_tot, 
        title="Average time of breastfeeding sessions between 06:00 to 06:00",
        scale=1/60,
        ylabel="Duration (minutes)"
    )
    slack.post_file("total_breatfeeding_time.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    mrk_down_message = make_duration_status_text(db_conn, "feed")
    return slack.response(mrk_down_message, response_type="in_channel")


def analyze_timeline(db_conn):
    df = an.merge_duration_tables(db_conn, tables=["feed", "sleep"])    
    plot_buffer = an.timeline_plot(df, title="Timeline of breastfeeding and sleep")
    slack.post_file("timeline.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    return slack.empty_response()


def handle_feed_status(args, db_conn):
    mrk_down_message = make_duration_status_text(db_conn, "feed")
    return slack.response(mrk_down_message, response_type="in_channel")


def create_feed_record(args, db_conn):
    return create_duration_record(args, db.create_feed, db_conn)

def handle_sleep_request(args, db_conn):
    if args is None:
        resp = slack.response(FEED_HELP, response_type="ephemeral")
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
    n = args[1] if len(args) == 2 else DEFAULT_N_LIST
    rows = db.get_latest_sleep_records(db_conn, n)
    rows = [format_duration_row(row) for row in rows]
    colnames = ["id", "from", "to", "duration", "created_at"]
    table_str = slack.table(rows, colnames)
    msg_text = f"*{n} latest sleeping records:*\n{table_str}"
    return slack.response(msg_text, response_type="ephemeral")

def handle_sleep_analyze(args, db_conn):
    if args[1] in {"tot", "total"}:
        return analyze_sleep_total(db_conn)
    elif args[1] in {"avg", "average"}:
        return analyze_sleep_avg(db_conn)
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
    df_agg_tot = an.total_duration_per_day(db_conn, "sleep")
    plot_buffer = an.duration_plot(
        df_agg_tot, 
        title="Average duration of each sleep period between 06:00 to 06:00",
        scale=1/3600,
        ylabel="Duration (hours)"
    )
    slack.post_file("total_sleeping_time.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    mrk_down_message = make_duration_status_text(db_conn, "sleep")
    return slack.response(mrk_down_message, response_type="in_channel")


def handle_sleep_status(args, db_conn):
    mrk_down_message = make_duration_status_text(db_conn, "sleep")
    return slack.response(mrk_down_message, response_type="in_channel")


def create_duration_record(args, create_db_record, db_conn):
    from_time, to_time = parse_duration_args(args)
    try:
        duration = to_time - from_time
    except TypeError:
        duration = None
    _validate_duration(duration)
    return create_db_record(db_conn, (from_time, to_time, duration)), duration


def make_duration_status_text(db_conn, table, latest_id=None):
    status_text = []
    if latest_id:
        latest_duration = db._get_duration_record_by_id(db_conn, table, latest_id)[3]
        status_text.append(f"Duration *{format_duration(latest_duration)}*")    
    latest_date, latest_tot_duration = an.latest_daily_total_duration(db_conn, table)
    status_text.append(f"Total duration on {latest_date.strftime('%A %d/%m')}: *{format_duration(latest_tot_duration)}*")
    return "\n".join(status_text)


def _validate_duration(duration):
    if duration is not None:
        assert (
            timedelta_to_seconds(duration) > 0
        ), "Duration must be positive. Got from_time '{from_time}' and to_time: '{to_time}' which gives a duration of '{duration}' seconds."


def parse_duration_args(args):
    from_time = dp.parse(args[0])
    try:
        to_time = args[1]
        to_time = dp.parse(to_time)
    except IndexError:
        to_time = None
    return from_time, to_time


def format_duration_row(row: tuple):
    id, from_time, to_time, duration, created_at, updated_at = row
    from_time = format_timestamp(from_time, short=True)
    to_time = format_timestamp(to_time, short=True)
    duration = format_duration(duration)
    created_at = format_timestamp(created_at)
    updated_at = format_timestamp(updated_at)
    return id, from_time, to_time, duration, created_at


def handle_weight_request(args, db_conn):
    if args is None:
        resp = slack.response(WEIGHT_HELP, response_type="ephemeral")
    elif args[0] in {"d", "del", "delete"}:
        resp = handle_delete_weight(args, db_conn)
    elif args[0] == "analyze":
        resp = handle_weight_analyze(args, db_conn)
    elif is_timestamp(args[0]):
        resp = handle_weight_create(args, db_conn)
    else:
        raise ValueError("Not valid args: {args}")
    return resp


def handle_weight_create(args, db_conn):
    weight_id = create_weight_record(args, db_conn)
    mrk_down_message = f":weight_lifter: Weight record created with Id: *{weight_id}*.\n"
    resp = slack.response(mrk_down_message)
    return resp


def create_weight_record(args, db_conn):
    timestamp, weight_in_grams = args
    timestamp = dp.parse(timestamp)
    weight_in_grams = int(weight_in_grams)
    assert weight_in_grams > 0, "Weight must be positive"
    assert weight_in_grams < 20000, "Weight must be less than 20kg"
    return db.create_weight(db_conn, (timestamp, weight_in_grams))


def handle_delete_weight(args, db_conn):
    weight_id = args[1]
    db.delete_feed(db_conn, weight_id)
    mrk_down_message = (
        f"Weight record with Id: *{weight_id}* deleted :wastebasket:"
    )
    resp = slack.response(mrk_down_message)
    return resp


def handle_weight_analyze(args, db_conn):
    df = an.weight_growth_df(db_conn)
    plot_buffer = an.growth_curves_plot(df)
    slack.post_file("weight.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    mrk_down_message = f"Latest weight measure at {df.iloc[-1]['weight']} g"
    return slack.response(mrk_down_message, response_type="in_channel")


def is_timestamp(s):
    out = dp.parse(s)
    return out is not None
