import sys
import csv
import re
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("csv1", help="Filepath to he first CSV file to join with.")
parser.add_argument("csv2", help="Filepath to the second CSV file to join with.")
parser.add_argument("-o", "--output", help="The filepath to output the resulting csv to.")
arguments = parser.parse_args()

infile1 = open(arguments.csv1)
infile2 = open(arguments.csv2)
csv_1 = csv.DictReader(infile1)
csv_2 = csv.DictReader(infile2)
csv_2.fieldnames = [string.split(".")[0] for string in csv_2.fieldnames]
joined_rows = []
for row in csv_2:
    joined_row = {}.fromkeys(csv_1.fieldnames, None)
    for key in row:
        if key in joined_row:
            joined_row[key] = row[key]
        else:
            if re.match("BlogsRead\[[0-9]+\]", key):
                nkey = "BlogsRead2[" + str(int(key.split("[")[1][:-1]) - 9) + "]"
            elif re.match("BlogsRead\[SQ[0-9]+\]", key):
                nkey = re.sub("BlogsRead\[(SQ[0-9]+)\]", "BlogsReadWriteIn[\g<1>]", key)
            elif re.match("StoriesRead\[[0-9]+\]", key):
                nkey = "StoriesRead2[" + str(int(key.split("[")[1][:-1]) - 9) + "]"
            if nkey in joined_row:
                joined_row[nkey] = row[key]
    joined_rows.append(joined_row)

if arguments.output:
    outfile = open(arguments.output, "w")
else:
    outfile = sys.stdout

outwriter = csv.DictWriter(outfile, csv_1.fieldnames)
outwriter.writeheader()
for row in csv_1:
    outwriter.writerow(row)
for row in joined_rows:
    outwriter.writerow(row)
