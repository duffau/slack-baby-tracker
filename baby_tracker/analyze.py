import io
import pandas as pd
from matplotlib import pyplot as plt

TIMESTAMP_COLUMNS = ["from_time", "to_time", "created_at", "updated_at"]

def total_duration_per_day(db_conn, table, offset="6Hours"):
    df = df_from_db_table(db_conn, table)
    df.duration = pd.to_timedelta(df.duration, unit="S")
    agg = df.resample('D', on='from_time', offset=offset).duration.sum()
    return agg

def avg_duration_per_day(db_conn, table, offset="6Hours"):
    df = df_from_db_table(db_conn, table)
    agg = df.resample('D', on='from_time', offset=offset)[["duration"]].mean()
    agg.duration = pd.to_timedelta(agg.duration, unit="S")
    return agg


def df_from_db_table(db_conn, table):
    return pd.read_sql_query(f"SELECT * FROM {table};", db_conn, parse_dates=TIMESTAMP_COLUMNS, index_col="id")


def plot_to_buffer():
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf
