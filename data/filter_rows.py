import csv
import sys

csv_filename = sys.argv[1] 

try:
    first_row = int(sys.argv[2]) - 1
except IndexError:
    first_row = None

try:
    last_row  = int(sys.argv[3]) - 1
except IndexError:
    last_row  = None



with open(csv_filename) as csv_file:
    reader = csv.reader(csv_file)
    header = reader.__next__() 
    rows = [row for row in reader]


rows = rows[first_row:last_row]

writer = csv.writer(sys.stdout)
writer.writerow(header)
writer.writerows(rows) 
