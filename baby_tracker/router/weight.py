import dateparser as dp

from baby_tracker import db
from baby_tracker import slack
from baby_tracker import analyze as an
from baby_tracker.utils import is_timestamp, format_timestamp

from .config import SLACK_OAUTH_TOKEN, CHANNEL_ID, DEFAULT_N_LIST

WEIGHT_HELP = """
*Examples*:
`/w`  _This help text_
`/w 2021-05-18 3254` _Register weight in grams at given date_
`/w d 71` _Delete weight record with id=71_
`/w analyze` _Plot growth curves_
"""


def handle_weight_request(args, db_conn):
    if args is None:
        resp = slack.response(WEIGHT_HELP, response_type="ephemeral")
    elif args[0] in {"d", "del", "delete"}:
        resp = handle_delete_weight(args, db_conn)
    elif args[0] in {"ls", "list"}:
        resp = handle_list_weight(args, db_conn)
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
    db.delete_weight_record(db_conn, weight_id)
    mrk_down_message = (
        f"Weight record with Id: *{weight_id}* deleted :wastebasket:"
    )
    resp = slack.response(mrk_down_message)
    return resp


def handle_list_weight(args, db_conn):
    n = int(args[1]) if len(args) == 2 else DEFAULT_N_LIST
    rows = db.get_latest_weight_records(db_conn, n)
    rows = [format_weight_row(row) for row in rows]
    colnames = ["date", "weight"]
    table_str = slack.table(rows, colnames)
    msg_text = f"*{n} latest weight records:*\n{table_str}"
    return slack.response(msg_text, response_type="ephemeral")


def handle_weight_analyze(args, db_conn):
    df = an.weight_growth_df(db_conn)
    plot_buffer = an.growth_curves_plot(df)
    slack.post_file("weight.png", plot_buffer, oauth_token=SLACK_OAUTH_TOKEN, channel_id=CHANNEL_ID)
    mrk_down_message = f"Latest weight measure at {df.iloc[-1]['weight']} g"
    return slack.response(mrk_down_message, response_type="in_channel")


def format_weight_row(row):
    _id, timestamp, weight, created_at, updated_at = row
    timestamp = format_timestamp(timestamp)
    weight = f"{weight}g"
    return timestamp, weight
