import datetime
import io
import pandas as pd
from matplotlib import pyplot as plt
from datetime import timedelta
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from pandas.core.frame import DataFrame

from baby_tracker.utils import format_duration, format_timestamp
from baby_tracker.db import to_iso

TIMESTAMP_COLUMNS = ["from_time", "to_time", "created_at", "updated_at"]
START_OF_DAY = datetime.time.fromisoformat("06:00")

def total_duration_per_day(db_conn, table, offset="6Hours"):
    df = df_from_db_table(db_conn, table)
    agg = df.resample('D', on='from_time', offset=offset)[["duration"]].sum()
    return agg

def latest_daily_total_duration(db_conn, table):
    df_agg_tot = total_duration_per_day(db_conn, table)
    last_date = df_agg_tot.index[-1]
    last_duration = timedelta(seconds=df_agg_tot.duration[-1])
    return last_date, last_duration

def avg_duration_per_day(db_conn, table, offset="6Hours"):
    df = df_from_db_table(db_conn, table)
    agg = df.resample('D', on='from_time', offset=offset)[["duration"]].mean()
    return agg


def df_from_db_table(db_conn, table, cutoff_timestamp:datetime=None):
    if cutoff_timestamp is None:
        return pd.read_sql_query(f"SELECT * FROM {table};", db_conn, parse_dates=TIMESTAMP_COLUMNS, index_col="id")
    else:
        return pd.read_sql_query(f"SELECT * FROM {table} WHERE created_at > {to_iso(cutoff_timestamp)};", db_conn, parse_dates=TIMESTAMP_COLUMNS, index_col="id")


def merge_duration_tables(db_conn, tables, n_days=3):
    n_days_ago = datetime.date.today() - timedelta(days=n_days)
    cutoff_timestamp = datetime.combine(n_days_ago, START_OF_DAY) 
    dfs = [df_from_db_table(db_conn, table, cutoff_timestamp) for table in tables]
    for df, table in zip(dfs, tables):
        df["activity"] = table
    merged_df = pd.concat(dfs, ignore_index=True)
    return merged_df


def duration_plot(df, title=None, scale=1/60, kind="bar", ylabel="Duration (minutes)"):
    df.duration *= scale
    fig, ax = plt.subplots()
    df.plot(title=title, kind=kind, ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels([x.strftime("%m-%d %a") for x in df.index], rotation=90)
    plt.tight_layout()
    return plot_to_buffer(fig)


def timeline_plot(df: DataFrame, title=None, from_var="from_time", to_var="to_time", duration_var="duration", activity_var="activity"):
    df.dropna(inplace=True, subset=[from_var, to_var, activity_var])
    df.sort_values(by=duration_var, inplace=True, ascending=False)
    colors = ('tab:blue', 'tab:orange', 'tab:green', 'tab:red')
    unique_activities = list(df[activity_var].unique())
    fig, ax = plt.subplots()
    time_points = df[[from_var, to_var]].to_numpy() 
    time_points = [(ft, tt-ft) for ft,tt in time_points]
    facecolors = [colors[unique_activities.index(activity)] for activity in df[activity_var]] 
    ax.broken_barh(time_points, (0, 10), facecolors=facecolors)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %a"))
    ax.xaxis.set_tick_params(rotation=90)
    ax.get_yaxis().set_visible(False)
    for from_time, duration in time_points:
        duration_sec = duration.astype('timedelta64[s]').item().total_seconds()
        ax.text(from_time+duration/2, 5, format_duration(duration_sec), rotation="vertical", va="center",ha="center")
    legend_handles = [ mpatches.Patch(color=colors[i], label=activity) for i, activity in enumerate(unique_activities)]
    plt.legend(handles=legend_handles)
    plt.tight_layout()
    return plot_to_buffer(fig)


def plot_to_buffer(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf
