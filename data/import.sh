#!/bin/bash
set -e

SQL_CREATE_FEED_TABLE='CREATE TABLE IF NOT EXISTS feed (
id integer PRIMARY KEY,
from_time text,
to_time text,
duration int,
created_at text,
updated_at text);'

SQL_CREATE_SLEEP_TABLE='CREATE TABLE IF NOT EXISTS sleep (
id integer PRIMARY KEY,
from_time text,
to_time text,
duration int,
created_at text,
updated_at text);'

.venv/bin/python3 ./data/transform_csv.py ./data/feed_slack_records.csv ./data/_feed_slack_records.csv
.venv/bin/python3 ./data/transform_csv.py ./data/sleep_slack_records.csv ./data/_sleep_slack_records.csv
.venv/bin/python3 ./data/filter_rows.py ./data/feed.csv 75 > ./data/_feed.csv
.venv/bin/python3 ./data/filter_rows.py ./data/sleep.csv > ./data/_sleep.csv
.venv/bin/python3 ./data/combine_table_csvs.py ./data/_feed.csv ./data/_feed_slack_records.csv ./data/_feed.csv
.venv/bin/python3 ./data/combine_table_csvs.py ./data/_sleep.csv ./data/_sleep_slack_records.csv ./data/_sleep.csv

sqlite3 db.sqlite <<EOF
${SQL_CREATE_FEED_TABLE}
${SQL_CREATE_SLEEP_TABLE}
.mode csv
.import --skip 1 ./data/_feed.csv feed
.import --skip 1 ./data/_sleep.csv sleep
UPDATE feed SET from_time = NULL WHERE from_time = 'NULL';
UPDATE feed SET to_time = NULL WHERE to_time = 'NULL';
UPDATE feed SET duration = NULL WHERE duration = 'NULL';
UPDATE feed SET created_at = NULL WHERE created_at = 'NULL';
UPDATE feed SET updated_at = NULL WHERE updated_at = 'NULL';

UPDATE sleep SET from_time = NULL WHERE from_time = 'NULL';
UPDATE sleep SET to_time = NULL WHERE to_time = 'NULL';
UPDATE sleep SET duration = NULL WHERE duration = 'NULL';
UPDATE sleep SET created_at = NULL WHERE created_at = 'NULL';
UPDATE sleep SET updated_at = NULL WHERE updated_at = 'NULL';
EOF
