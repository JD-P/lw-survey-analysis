# Output various stats about a csv file to stdout
import csv
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("csvfile", help="Filepath to the csv file to stat.")
arguments = parser.parse_args()

with open(arguments.csvfile) as infile:
    inreader = csv.DictReader(infile)
    row_count = 0
    column_count = len(inreader.fieldnames)
    for row in inreader:
        row_count += 1

print(row_count)
print(column_count)
