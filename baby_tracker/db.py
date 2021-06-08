import sqlite3
from sqlite3 import Error
import logging
from datetime import datetime, timedelta
import baby_tracker.utils as ut  

logger = logging.getLogger(__name__)

ISO_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def create_connection(db_file=":memory:"):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.info(sqlite3.version)
    except Error as e:
        logger.error(e)
    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    c = conn.cursor()
    c.execute(create_table_sql)


SQL_CREATE_FEED_TABLE = """ CREATE TABLE IF NOT EXISTS feed (
                                    id integer PRIMARY KEY,
                                    from_time text,
                                    to_time text,
                                    duration int,
                                    created_at text,
                                    updated_at text
                                ); """

SQL_CREATE_SLEEP_TABLE = """ CREATE TABLE IF NOT EXISTS sleep (
                                    id integer PRIMARY KEY,
                                    from_time text,
                                    to_time text,
                                    duration int,
                                    created_at text,
                                    updated_at text
                                ); """

SQL_CREATE_WEIGHT_TABLE = """ CREATE TABLE IF NOT EXISTS weight (
                                    id integer PRIMARY KEY,
                                    timestamp text NOT NULL,
                                    weight int NOT NULL,
                                    created_at text,
                                    updated_at text
                                ); """

SQL_CREATE_POOP_TABLE = """ CREATE TABLE IF NOT EXISTS poop (
                                    id integer PRIMARY KEY,
                                    timestamp text NOT NULL,
                                    created_at text,
                                    updated_at text
                                ); """


def init_db(db_file: str):
    conn = create_connection(db_file)
    create_table(conn, SQL_CREATE_FEED_TABLE)
    create_table(conn, SQL_CREATE_SLEEP_TABLE)
    create_table(conn, SQL_CREATE_WEIGHT_TABLE)
    create_table(conn, SQL_CREATE_POOP_TABLE)
    return conn


def create_feed(conn, feed):
    return _create_duration_record(conn, feed, "feed")


def create_sleep(conn, sleep):
    return _create_duration_record(conn, sleep, "sleep")


def _create_duration_record(conn, duration_record, table):
    """
    Create a new generic duration type record into the specified table
    :param conn:
    :param duration_record:
    :param table:
    :return: id
    """
    sql = f"""INSERT INTO {table}(from_time,to_time,duration,created_at,updated_at)
              VALUES(?,?,?,?,?) """
    cur = conn.cursor()
    current_timestamp = to_iso(datetime.now())
    from_time, to_time, duration = duration_record
    if from_time is not None:
        from_time = to_iso(from_time)
    if to_time is not None:
        to_time = to_iso(to_time)
    if duration is not None:
        duration = ut.timedelta_to_seconds(duration)
    row = (from_time, to_time, duration, current_timestamp, None)
    cur.execute(sql, row)
    conn.commit()
    return cur.lastrowid

def create_weight(conn, weight_rec):
    sql = f"""INSERT INTO weight(timestamp,weight,created_at,updated_at)
              VALUES(?,?,?,?) """
    cur = conn.cursor()
    current_timestamp = to_iso(datetime.now())
    timestamp, weight = weight_rec
    if timestamp is not None:
        timestamp = to_iso(timestamp)
    row = (timestamp, weight, current_timestamp, None)
    cur.execute(sql, row)
    conn.commit()
    return cur.lastrowid


def create_poop(conn, poop_rec):
    sql = f"""INSERT INTO poop(timestamp,created_at,updated_at)
              VALUES(?,?,?) """
    cur = conn.cursor()
    current_timestamp = to_iso(datetime.now())
    timestamp = poop_rec
    if timestamp is not None:
        timestamp = to_iso(timestamp)
    row = (timestamp, current_timestamp, None)
    cur.execute(sql, row)
    conn.commit()
    return cur.lastrowid


def get_latest_feed_records(conn, n=5):
    return _get_latest_duration_records(conn, "feed", n)


def get_latest_sleep_records(conn, n=5):
    return _get_latest_duration_records(conn, "sleep", n)


def _get_latest_duration_records(conn, table, n):
    cur = conn.cursor()
    sql = f"SELECT * FROM {table} ORDER BY created_at desc LIMIT {n}"
    cur.execute(sql)
    rows = cur.fetchall()
    transformed_rows = []
    for row in rows:
        transformed_row = transform_duration_row(row)
        transformed_rows.append(transformed_row)
    return transformed_rows

def get_latest_weight_records(conn, n=None):
    cur = conn.cursor()
    limit = f"LIMIT {n}" if n is not None else ""
    sql = f"SELECT * FROM weight ORDER BY timestamp desc " + limit
    cur.execute(sql)
    rows = cur.fetchall()
    transformed_rows = []
    for row in rows:
        transformed_row = transform_weight_row(row)
        transformed_rows.append(transformed_row)
    return transformed_rows


def get_latest_poop_records(conn, n=None):
    cur = conn.cursor()
    limit = f"LIMIT {n}" if n is not None else ""
    sql = f"SELECT * FROM poop ORDER BY timestamp desc " + limit
    cur.execute(sql)
    rows = cur.fetchall()
    transformed_rows = []
    for row in rows:
        transformed_row = transform_poop_row(row)
        transformed_rows.append(transformed_row)
    return transformed_rows


def get_feed_record_by_id(conn, id):
    return _get_duration_record_by_id(conn, "feed", id)


def get_sleep_record_by_id(conn, id):
    return _get_duration_record_by_id(conn, "sleep", id)


def _get_duration_record_by_id(conn, table, id):
    cur = conn.cursor()
    sql = f"SELECT * FROM {table} WHERE id = {id}"
    cur.execute(sql)
    rows = cur.fetchall()
    if rows:
        transformed_row = transform_duration_row(rows[0])
        return transformed_row
    else:
        return None

def get_latest_feed_record_with_null_to_time(conn):
    return _get_latest_duration_record_with_null_to_time(conn, "feed")


def get_latest_sleep_record_with_null_to_time(conn):
    return _get_latest_duration_record_with_null_to_time(conn, "sleep")


def _get_latest_duration_record_with_null_to_time(conn, table):
    cur = conn.cursor()
    sql = f"SELECT * FROM {table} WHERE to_time IS NULL ORDER BY created_at desc LIMIT 1;"
    cur.execute(sql)
    rows = cur.fetchall()
    if rows:
        transformed_row = transform_duration_row(rows[0])
        return transformed_row
    else:
        return None


def transform_duration_row(row):
    id, from_time, to_time, duration, created_at, updated_at = row
    from_time = to_datetime(from_time)
    to_time = to_datetime(to_time)
    duration = seconds_to_timedelta(duration)
    created_at = to_datetime(created_at)
    updated_at = to_datetime(updated_at)
    transformed_row = id, from_time, to_time, duration, created_at, updated_at
    return transformed_row


def transform_weight_row(row):
    id, timestamp, weight, created_at, updated_at = row
    timestamp = to_datetime(timestamp)
    created_at = to_datetime(created_at)
    updated_at = to_datetime(updated_at)
    transformed_row = id, timestamp, weight, created_at, updated_at
    return transformed_row

def transform_poop_row(row):
    id, timestamp, created_at, updated_at = row
    timestamp = to_datetime(timestamp)
    created_at = to_datetime(created_at)
    updated_at = to_datetime(updated_at)
    transformed_row = id, timestamp, created_at, updated_at
    return transformed_row


def delete_feed(conn, feed_id):
    return _delete_duration_record(conn, feed_id, "feed")


def delete_sleep(conn, sleep_id):
    return _delete_duration_record(conn, sleep_id, "sleep")


def _delete_duration_record(conn, record_id, table):
    """
    Create a new generic duration type record into the specified table
    :param conn:
    :param duration_record:
    :param table:
    :return: id
    """
    sql = f"""DELETE from {table} where id = {record_id}"""
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    return record_id


def delete_weight_record(conn, record_id):
    sql = f"""DELETE from weight where id = {record_id}"""
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    return record_id


def delete_poop_record(conn, record_id):
    sql = f"""DELETE from poop where id = {record_id}"""
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    return record_id


def update_feed(conn, feed_id, feed_record):
    return _update_duration_record(conn, "feed", feed_id, feed_record)


def update_sleep(conn, sleep_id, sleep_record):
    return _update_duration_record(conn, "sleep", sleep_id, sleep_record)


def _update_duration_record(conn, table, id, duration_record):
    sql = f"""UPDATE {table} 
                SET from_time = ?,
                    to_time = ?, 
                    duration = ?,
                    updated_at = ?
                WHERE id = ?"""
    cur = conn.cursor()
    current_timestamp = to_iso(datetime.now())
    from_time, to_time, duration = duration_record
    if from_time is not None:
        from_time = to_iso(from_time)
    if to_time is not None:
        to_time = to_iso(to_time)
    if duration is not None:
        duration = ut.timedelta_to_seconds(duration)
    row = (from_time, to_time, duration, current_timestamp, id)
    cur.execute(sql, row)
    conn.commit()
    return id

def to_iso(timestamp: datetime):
    return timestamp.strftime(ISO_FORMAT)


def to_datetime(timestamp: str):
    if timestamp is None:
        return None     
    else:
        return datetime.strptime(timestamp, ISO_FORMAT)


def seconds_to_timedelta(seconds: int):
    if seconds is None:
        return None
    else:
        return timedelta(seconds=seconds)

def list_feed_records(conn, limit=5):
    return _list_duration_records(conn, table="feed", limit=limit)


def list_sleep_records(conn, limit=5):
    return _list_duration_records(conn, table="sleep", limit=limit)


def _list_duration_records(conn, table, limit):
    sql = f"""SELECT from_time,to_time,duration,created_at,updated_at from {table} LIMIT {limit}"""
    cur = conn.cursor()
    cur.execute(sql)
    records = cur.fetchall()
    return records
