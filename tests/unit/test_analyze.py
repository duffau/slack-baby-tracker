from baby_tracker import db
from baby_tracker import analyze as an
from datetime import datetime, time, timedelta
from pprint import pprint
import matplotlib.pyplot as plt 
import sqlite3
import requests
import io

def generate_duration_records(durations_minutes, spacing=timedelta(minutes=60), start_time=datetime(2021, 5, 18, 6, 38)):
    records = []
    from_time = start_time
    for duration in durations_minutes:
        from_time += spacing
        duration = timedelta(minutes=duration) if duration else None
        to_time = from_time + duration if duration else None
        record = (from_time, to_time, duration)
        records.append(record)
    return records 

# db_conn = db.init_db(db_file=":memory:")
db_conn = sqlite3.connect("../../../baby-tracker/db.sqlite")

feeds = generate_duration_records(durations_minutes= [15,10,5, 15,25,65,None,80], spacing=timedelta(hours=20))
# for feed in feeds:
#     db.create_feed(db_conn, feed)

# for record in db.list_feed_records(db_conn):
#     print(record)

df = an.avg_duration_per_day(db_conn, "feed")
print(df)
df.plot()
plt.savefig("feed_avg.png")
plt.close()
df = an.total_duration_per_day(db_conn, "feed")
print(df)
df.plot()
plt.savefig("feed_total.png")
plt.close()

df = an.avg_duration_per_day(db_conn, "sleep")
print(df)
df.plot()
plt.savefig("sleep_avg.png")
plt.close()
df = an.total_duration_per_day(db_conn, "sleep")
print(df)
df.plot()
plt.savefig("sleep_total.png")
plt.close()
