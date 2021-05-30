import csv
from datetime import datetime
import sys

input_csv_filename = sys.argv[1]
output_csv_filename = sys.argv[2]

INPUT_DT_FORMAT = "%Y-%m-%d %H:%M"
OUTPUT_DT_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

def format_record(from_time, to_time, created_at):
    from_time = from_time.strftime(OUTPUT_DT_FORMAT) if from_time != "NULL" else "NULL"
    to_time = to_time.strftime(OUTPUT_DT_FORMAT) if to_time != "NULL" else "NULL"
    created_at = created_at.strftime(OUTPUT_DT_FORMAT) if created_at != "NULL" else "NULL"
    return from_time, to_time, created_at


transformed_csv = []
with open(input_csv_filename) as csvfile:
    reader = csv.reader(csvfile)
    reader.__next__()
    for i, row in enumerate(reader):
        try:
            from_time = datetime.strptime(row[0], INPUT_DT_FORMAT)
        except:
            from_time = row[0]

        try:
            to_time = datetime.strptime(row[1], INPUT_DT_FORMAT)
        except:
            to_time = row[1]

        try:
            duration = (to_time - from_time).seconds
        except:
            duration = "NULL"
        created_at = datetime.strptime(row[2], INPUT_DT_FORMAT)
        updated_at = "NULL"
        print("duration:", duration, row)
        from_time, to_time, created_at = format_record(from_time, to_time, created_at)
        transformed_csv.append(
            (i + 1, from_time, to_time, duration, created_at, updated_at)
        )


with open(output_csv_filename, "w") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerows(transformed_csv)
