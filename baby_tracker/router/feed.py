import dateparser as dp

from baby_tracker import db
from baby_tracker import slack
from baby_tracker import analyze as an
from baby_tracker.utils import format_timestamp, is_timestamp
from baby_tracker.router._duration import create_duration_record, make_duration_status_text, format_duration_row, format_timestamp, _validate_duration, analyze_timeline

from .config import DEFAULT_N_LIST, SLACK_OAUTH_TOKEN, CHANNEL_ID


FEED_HELP = """
*Examples*:
`/f`  _This help text_
`/f 12:30 16:45` _Register breastfeeding between two time points_
`/f ls 5` _List 5 latest breastfeeding entries_
`/f d 71` _Delete breastfeeding record with id=71_
`/f analyze` Returns plots and stats of breastfeeding bahaviour.
"""



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


def handle_feed_status(args, db_conn):
    mrk_down_message = make_duration_status_text(db_conn, "feed")
    return slack.response(mrk_down_message, response_type="in_channel")


def create_feed_record(args, db_conn):
    return create_duration_record(args, db.create_feed, db_conn)
