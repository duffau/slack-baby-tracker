from baby_tracker import db
from baby_tracker import analyze as an
from datetime import datetime, time, timedelta
from pprint import pprint
import matplotlib.pyplot as plt 
import sqlite3
import requests
import io
import pandas as pd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def generate_duration_records(durations_minutes, spacing=timedelta(minutes=60), start_time=datetime(2021, 5, 18, 6, 38)):
    records = []
    to_time = start_time
    for duration in durations_minutes:
        from_time = to_time + spacing
        duration = timedelta(minutes=duration) if duration else None
        to_time = from_time + duration if duration else None
        record = (from_time, to_time, duration)
        records.append(record)
    return records 

# db_conn = db.init_db(db_file="./db.sqlite")
db_conn = sqlite3.connect("./db.sqlite")

# feeds = generate_duration_records(durations_minutes=[10,10,10], spacing=timedelta(minutes=20), start_time=datetime(2021, 5, 18, 6, 00))
# for feed in feeds:
#     db.create_feed(db_conn, feed)

# sleeps = generate_duration_records(durations_minutes= [20,20,20], spacing=timedelta(minutes=10), start_time=datetime(2021, 5, 18, 6, 10))
# for sleep in sleeps:
#     db.create_sleep(db_conn, sleep)

# df = an.total_duration_per_day(db_conn, "feed")
# plot_buffer = an.duration_plot(df)

# df = an.avg_duration_per_day(db_conn, "feed")
# plot_buffer = an.duration_plot(df)

df = an.merge_duration_tables(db_conn, tables=["feed", "sleep"])
print(df.dtypes)
print(df)
plot_buffer = an.timeline_plot(df)

with open("timeline.png", "wb") as plot_file:
    plot_file.write(plot_buffer.read())

df = an.weight_growth_df(db_conn)
print(df.dtypes)
print(df)
plot_buffer = an.growth_curves_plot(df)

with open("weight_growth.png", "wb") as plot_file:
    plot_file.write(plot_buffer.read())
