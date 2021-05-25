from baby_tracker import serve, db
from datetime import timedelta


def test_handle_feed_request():
    args = ("12:30", "12:35")
    db_conn = db.init_db(db_file=":memory:")
    resp = serve.handle_feed_request(args, db_conn)
    print(resp)
    db_conn.close()


def test_handle_feed_request_no_end_time():
    args = ("12:30",)
    db_conn = db.init_db(db_file=":memory:")
    resp = serve.handle_feed_request(args, db_conn)
    print(resp)
    db_conn.close()
