import sqlite3
import pandas as pd

TIMESTAMP_COLUMNS = ["from_time", "to_time", "created_at", "updated_at"]


def df_from_db_table(db_conn, table):
    return pd.read_sql_query(
        f"SELECT * FROM {table};",
        db_conn,
        parse_dates=TIMESTAMP_COLUMNS,
        index_col="id",
    )


con = sqlite3.connect("./db.sqlite")
df = df_from_db_table(con, "sleep")
print(df.dtypes)
