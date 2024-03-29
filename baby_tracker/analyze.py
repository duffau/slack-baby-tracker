import datetime
import io
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
from datetime import timedelta, date
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from pandas.core.frame import DataFrame
from labellines import labelLines

from baby_tracker.utils import format_duration, format_timestamp
from baby_tracker.db import to_iso
import baby_tracker.utils as ut

TIMESTAMP_COLUMNS = ["from_time", "to_time", "created_at", "updated_at", "timestamp"]
START_OF_DAY = datetime.time.fromisoformat("06:00")
BIRTH_DATE = datetime.date(2024, 1, 24)

matplotlib.use('Agg')

def total_duration_per_day(db_conn, table, offset="6Hours"):
    df = df_from_db_table(db_conn, table)
    agg = df.resample('D', on='from_time', offset=offset)[["duration"]].sum()
    return agg

def latest_daily_total_duration(db_conn, table):
    df_agg_tot = total_duration_per_day(db_conn, table)
    last_date = df_agg_tot.index[-1]
    last_duration = timedelta(seconds=int(df_agg_tot.duration.iloc[-1]))
    return last_date, last_duration

def avg_duration_per_day(db_conn, table, offset="6Hours"):
    df = df_from_db_table(db_conn, table)
    agg = df.resample('D', on='from_time', offset=offset)[["duration"]].mean()
    return agg

def count_per_day(db_conn, table, offset="6Hours"):
    df = df_from_db_table(db_conn, table)
    agg = df.resample('D', on='from_time', offset=offset)[["duration"]].size()
    return agg


def latest_n_intervals(db_conn, table, n=3):
    df = df_from_db_table(db_conn, table, limit=n+1)
    df["time_interval"] = df["from_time"].diff()
    return df


def df_from_db_table(db_conn, table, cutoff_timestamp:datetime=None, limit:int=None):
    if limit is not None:
        limit = int(limit)
        limit_sql = f"LIMIT {limit}"
    else:
        limit_sql = ""

    if cutoff_timestamp is None:
        return pd.read_sql_query(f"SELECT * FROM {table} {limit_sql};", db_conn, parse_dates=TIMESTAMP_COLUMNS, index_col="id")
    else:
        return pd.read_sql_query(f"SELECT * FROM {table} WHERE datetime(created_at) > datetime('{to_iso(cutoff_timestamp)}') {limit_sql};", db_conn, parse_dates=TIMESTAMP_COLUMNS, index_col="id")



def merge_duration_tables(db_conn, tables, n_days=3):
    dfs = [get_duration_table(db_conn, table, n_days=n_days) for table in tables]
    for df, table in zip(dfs, tables):
        df["activity"] = table
    merged_df = pd.concat(dfs, ignore_index=True)
    return merged_df


def get_duration_table(db_conn, table, n_days=3, n_weeks=None):
    if n_weeks:
        cutoff_date = date.today() - timedelta(days=date.today().weekday(), weeks=n_weeks)
    else:
        cutoff_date = datetime.date.today() - timedelta(days=n_days-1)
    cutoff_timestamp = datetime.datetime.combine(cutoff_date, START_OF_DAY) 
    return df_from_db_table(db_conn, table, cutoff_timestamp)


def duration_plot(df, title=None, scale=1/60, kind="bar", ylabel="Duration (minutes)"):
    if scale != 1:
        df.duration *= scale
    fig, ax = plt.subplots()
    df.plot(title=title, kind=kind, ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels([x.strftime("%a %d/%m") for x in df.index], rotation=90)
    ax.set_axisbelow(True)
    ax.grid(axis="y")
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
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d/%m %H:%M"))
    ax.xaxis.set_tick_params(rotation=90)
    ax.get_yaxis().set_visible(False)
    for from_time, duration in time_points:
        duration_sec = duration.astype('timedelta64[s]').item().total_seconds()
        ax.text(from_time+duration/2, 5, format_duration(duration_sec), rotation="vertical", va="center",ha="center")
    timestamps = numpydt_to_datetime([ft for ft, dur in  time_points])
    min_timestamp = min(timestamps)
    timestamps = numpydt_to_datetime([ft+dur for ft, dur in  time_points])
    max_timestamp = max(timestamps)
    min_timestamp = datetime.datetime.combine(min_timestamp.date(), START_OF_DAY) 
    max_timestamp = datetime.datetime.combine(max_timestamp.date() + timedelta(days=1), START_OF_DAY)
    day_shifts = ut.datetime_range(start=min_timestamp, end=max_timestamp)
    for day_shift in day_shifts: 
        ax.vlines(day_shift, 0, 10,colors="black", linestyles='dashed')

    legend_handles = [ mpatches.Patch(color=colors[i], label=activity) for i, activity in enumerate(unique_activities)]
    plt.legend(handles=legend_handles)
    plt.tight_layout()
    return plot_to_buffer(fig)

def daily_duration_pattern_plot(df: DataFrame, title=None, from_var="from_time", to_var="to_time", duration_var="duration"):
    pass


def weight_growth_df(db_conn, birth_date=BIRTH_DATE):
    df = df_from_db_table(db_conn, "weight")
    df["age"] = (df.timestamp - pd.to_datetime(birth_date)).dt.days
    return df


def growth_curves_plot(df,  title=None, growth_variable="weight", sex="boy", baby_name="Oscar"):
    basename = {"weight": "weianthro"}.get(growth_variable)
    x_var = "age"
    ylabel = {"weight": "weight (g)"}.get(growth_variable)
    xlabel = {"weight": "age (days)"}.get(growth_variable)


    growth_curnves = pd.read_csv(f"./baby_tracker/growth-curves/{basename}_{sex}.csv")
    x_max = int(max(df[x_var])*1.25)
    growth_curnves = growth_curnves[growth_curnves[x_var] < x_max].copy()
    fig, ax = plt.subplots()
    if growth_curnves.empty:
        ax = empty_plot(ax, "No growth curve data found")
    else:
        ax = growth_curnves.plot(
            x=x_var,
            y=["p5", "p25", "p50", "p75", "p95"],
            style=["--", "--", "-", "--", "--"],
            lw=1,
            color="black",
            title=f"WHO {growth_variable} curves: {sex}",
            ax = ax
        )
        labelLines(fig.gca().get_lines(), zorder=2.5)
        ax = df.plot(x=x_var, y=growth_variable, label=baby_name, ax=ax, style="-o")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.get_legend().remove()
        ax.set_axisbelow(True)
        ax.grid(axis="y")
    fig.tight_layout()
    return plot_to_buffer(fig)

def numpydt_to_datetime(np_datetime):
    return [datetime.datetime.fromtimestamp(ts.astype('O')/1e9) for ts in np_datetime]

def plot_to_buffer(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def empty_plot(ax, text="No data found", color="red"):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.text(0.5, 0.5, text, horizontalalignment='center', verticalalignment='center', fontsize=20, color=color)
    return ax