import os
import traceback
from flask import Flask, request, jsonify, g

from baby_tracker import db
from baby_tracker import slack
from baby_tracker.router.feed import handle_feed_request
from baby_tracker.router.sleep import handle_sleep_request
from baby_tracker.router.weight import handle_weight_request
from baby_tracker.router.poop import handle_poop_request


HELP = """
This is the baby tracker.

*Examples*:
/f Register *breastfeeding*. Call command without arguments for help.
/sl Register *sleep*. Call command without arguments for help.
"""

DB_FILE = os.getenv("DB_FILE")

def parse_args(args_text):
    if args_text:
        return args_text.split()
    else:
        return None


app = Flask(__name__)


def get_db():
    db_conn = getattr(g, "_database", None)
    if db_conn is None:
        db_conn = g._database = db.init_db(db_file=DB_FILE)
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
    elif action == "poop":
        resp = handle_poop_request(args, db_conn)
    else:
        raise ValueError(f"action: '{action}' not recognized.")
    return resp


def help():
    resp = slack.response(HELP)
    return resp



