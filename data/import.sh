#!/bin/bash
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

python transform_csv.py feed_hist.csv
python transform_csv.py sleep_hist.csv

sqlite3 ../db.sqlite <<EOF
${SQL_CREATE_FEED_TABLE}
${SQL_CREATE_SLEEP_TABLE}
.mode csv
.import feed_hist_trans.csv feed
.import sleep_hist_trans.csv sleep
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
