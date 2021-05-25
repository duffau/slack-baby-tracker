import os
import traceback
from flask import Flask, request, jsonify, g
from datetime import datetime, timedelta
import dateparser as dp

from baby_tracker import db
from baby_tracker import slack


HELP = """
This is the Carla sleep and nursing tracker.

*Examples*:
/carla n 12:30 [12:45]: register nursing between two timestamps where the end point is optional.
"""
DEFAULT_N_LIST = 5


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
    if args[0] in {"d", "del", "delete"}:
        resp = handle_delete_feed(args, db_conn)
    elif args[0] in {"ls", "list"}:
        resp = handle_list_feeds(args, db_conn)
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
    feed_id, duration = create_feed_record(args, db_conn)
    mrk_down_message = f"Breastfeeding record created with Id: *{feed_id}* and duration *{format_duration(duration)}* :breast-feeding:"
    resp = slack.response(mrk_down_message)
    return resp


def create_feed_record(args, db_conn):
    return create_duration_record(args, db.create_feed, db_conn)

def handle_sleep_request(args, db_conn):
    if args[0] in {"d", "del", "delete"}:
        resp = handle_delete_sleep(args, db_conn)
    elif args[0] in {"ls", "list"}:
        resp = handle_list_sleeps(args, db_conn)
    elif is_timestamp(args[0]):
        resp = handle_sleep_create(args, db_conn)
    else:
        raise ValueError("Not valid args: {args}")
    return resp

def handle_sleep_create(args, db_conn):
    sleep_id, duration = create_sleep_record(args, db_conn)
    mrk_down_message = f"Sleep record created with Id: *{sleep_id}* and duration *{format_duration(duration)}* :sleeping:"
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


def create_duration_record(args, create_db_record, db_conn):
    from_time, to_time = parse_duration_args(args)
    try:
        duration = to_time - from_time
    except TypeError:
        duration = None
    _validate_duration(duration)
    return create_db_record(db_conn, (from_time, to_time, duration)), duration


def _validate_duration(duration):
    if duration is not None:
        assert (
            duration.seconds > 0
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
    from_time = format_timestamp(from_time)
    to_time = format_timestamp(to_time)
    duration = format_duration(duration)
    created_at = format_timestamp(created_at)
    updated_at = format_timestamp(updated_at)
    return id, from_time, to_time, duration, created_at


def format_timestamp(timestamp: datetime):
    try:
        return timestamp.strftime("%d/%m-%Y %H:%M")
    except AttributeError:
        return str(timestamp)

def format_duration(duration: timedelta):
    try:
        duration = duration.seconds
        hours, remainder = divmod(duration, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}"
    except AttributeError:
        return str(duration)


def handle_weight_request(args, db_conn):
    pass


def is_timestamp(s):
    out = dp.parse(s)
    return out is not None
