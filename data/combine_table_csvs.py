import sys
import csv

first_csv_filename = sys.argv[1]
second_csv_filename = sys.argv[2]
output_csv_filename = sys.argv[3]

all_rows = []

with open(first_csv_filename) as csv_file:
    csv_reader = csv.reader(csv_file)
    first_header = csv_reader.__next__()
    # Dropping id column
    first_rows = [row[1:] for row in csv_reader]


with open(second_csv_filename) as csv_file:
    csv_reader = csv.reader(csv_file)
    # Dropping id column
    second_rows = [row[1:] for row in csv_reader]


all_rows = first_rows + second_rows
# Sort on created_at column
all_rows = sorted(all_rows, key=lambda row: row[-2])
all_rows = [(i+1,*row) for i,row in enumerate(all_rows)]

with open(output_csv_filename, "w") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(first_header)
    csv_writer.writerows(all_rows)
