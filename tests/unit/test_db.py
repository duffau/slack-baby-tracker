from datetime import datetime
from baby_tracker import db

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def list_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [table_row[0] for table_row in tables]


def test_create_connection():
    conn = db.create_connection(db_file=":memory:")
    tables = list_tables(conn)
    assert tables == []
    conn.close()


def test_create_table():
    conn = db.create_connection(db_file=":memory:")
    db.create_table(conn, "CREATE TABLE mytable ( mycol );")
    db.create_table(conn, "CREATE TABLE myothertable ( mycol );")
    tables = list_tables(conn)
    assert tables == ["mytable", "myothertable"]
    conn.close()


def test_init_db():
    conn = db.init_db(db_file=":memory:")
    tables = list_tables(conn)
    assert tables == ["feed", "sleep"]
    conn.close()


def test_create_feed():
    conn = db.init_db(db_file=":memory:")
    from_time = datetime(2021, 5, 18, 6, 38, 30)
    to_time = datetime(2021, 5, 18, 6, 50, 20)
    duration = to_time - from_time
    feed = (from_time, to_time, duration)
    feed_id = db.create_feed(conn, feed)

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feed;")
    rows = cursor.fetchall()
    print(rows)
    assert feed_id == 1
    assert len(rows) == 1
    _id, _from_time, _to_time, _duration, _created_at, _updated_at = rows[0]
    assert _id == 1
    assert datetime.strptime(_from_time, TIMESTAMP_FORMAT) == from_time
    assert datetime.strptime(_to_time, TIMESTAMP_FORMAT) == to_time
    assert _duration == duration.seconds
    assert datetime.strptime(_created_at, TIMESTAMP_FORMAT) < datetime.now()
    assert _updated_at is None
    conn.close()
