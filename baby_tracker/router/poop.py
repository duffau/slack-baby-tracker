import dateparser as dp

from baby_tracker import db
from baby_tracker import slack
from baby_tracker import analyze as an
from baby_tracker.utils import format_timestamp, is_timestamp

from .config import SLACK_OAUTH_TOKEN, CHANNEL_ID, DEFAULT_N_LIST

POOP_HELP = f"""
*Examples*:
`/poop`  _This help text_
`/poop 2021-05-18` _Register poop at a given date_
`/poop 2021-05-18` _Register poop at a given date_
`/poop d 71` _Delete poop record with id=71_
`/poop ls` _List {DEFAULT_N_LIST} latests poops_
`/poop ls 10` _List 10 latests poops_
"""


def handle_poop_request(args, db_conn):
    if args is None:
        resp = slack.response(POOP_HELP, response_type="ephemeral")
    elif args[0] in {"d", "del", "delete"}:
        resp = handle_delete_poop(args, db_conn)
    elif args[0] in {"ls", "list"}:
        resp = handle_list_poop(args, db_conn)
    elif is_timestamp(args[0]):
        resp = handle_poop_create(args, db_conn)
    else:
        raise ValueError("Not valid args: {args}")
    return resp


def handle_poop_create(args, db_conn):
    poop_id = create_poop_record(args, db_conn)
    mrk_down_message = f":poop: poop record created with Id: *{poop_id}*.\n"
    resp = slack.response(mrk_down_message)
    return resp


def create_poop_record(args, db_conn):
    timestamp = args[0]
    timestamp = dp.parse(timestamp)
    return db.create_poop(db_conn, timestamp)


def handle_delete_poop(args, db_conn):
    poop_id = args[1]
    db.delete_poop_record(db_conn, poop_id)
    mrk_down_message = (
        f"poop record with Id: *{poop_id}* deleted :wastebasket:"
    )
    resp = slack.response(mrk_down_message)
    return resp


def handle_list_poop(args, db_conn):
    n = int(args[1]) if len(args) == 2 else DEFAULT_N_LIST
    rows = db.get_latest_poop_records(db_conn, n)
    rows = [format_poop_row(row) for row in rows]
    colnames = ["date"]
    table_str = slack.table(rows, colnames)
    msg_text = f"*{n} latest poop records:*\n{table_str}"
    return slack.response(msg_text, response_type="ephemeral")


def format_poop_row(row):
    _id, timestamp, created_at, updated_at = row
    timestamp = format_timestamp(timestamp)
    return (timestamp,)
