# made and placed in the public domain by Bartosz Wróblewski, sometimes known as bawr
import time
import calendar
import csv
import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filepath")
parser.add_argument("output")
arguments = parser.parse_args()
     
     
RF = open(arguments.filepath)
RD = csv.reader(RF)
     
rows = iter(RD)
head = next(rows)
     
     
def f(n):
    n = n.replace('[', '_')
    n = n.replace(']', '')
    return n
     
head = [f(n) for n in head]
     
     
rows = list(rows)
if (len(rows[-1]) == 0):
    rows.pop()
    
len_hdr = len(head)
len_min = min(len(r) for r in rows)
len_max = max(len(r) for r in rows)
     
print("Columns: %d (rows have between %d and %d)" % (len_hdr, len_min, len_max))
print("Rows: %d" % (len(rows),))
     
assert(len_hdr == len_min == len_max)
     
     
def has_ans(c):
    try:
        isnot_empty = "" != c.strip()
        isnot_na = "N/A" != c.strip()
        return (isnot_empty and isnot_na)
    except AttributeError:
        return True
     
def numeric(c):
    try:
        i = float(c)
    except ValueError:
        t = False
    else:
        t = True
    return t

for row in rows:
    try:
        row[1] = calendar.timegm(time.strptime(row[1], "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        row[1] = ""
    try:
        row[4] = calendar.timegm(time.strptime(row[4], "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        row[4] = ""
    try:
        row[5] = calendar.timegm(time.strptime(row[5], "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        row[5] = ""
rows_a = [[has_ans(c) for c in r] for r in rows]
rows_n = [[numeric(c) for c in r] for r in rows]

cols_a = [sum(t) for t in zip(*rows_a)] # answers in each column
cols_n = [sum(t) for t in zip(*rows_n)] # numbers in each column
cols_t = [(a == n) for a, n in zip(cols_a, cols_n)]

print("Numeric columns: %d" % (sum(cols_t),))
     
     
tb = "CREATE TABLE DATA"
tb += " (\n"
tb += ',\n'.join("%s %s" % (n, "REAL" if t else "TEXT") for n, t in zip(head, cols_t))
tb += "\n);"
     
ti = "INSERT INTO DATA VALUES"
ti += " ("
ti += ','.join(['?'] * len_hdr)
ti += ")"
     
db = sqlite3.connect(arguments.output)
db.execute(tb)
db.executemany(ti, rows)
db.commit()
db.row_factory = sqlite3.Row
print("Initializing blank entries to NULL...")
cursor = db.cursor()
cursor.execute("select * from data where rowid = 1;")
columns = cursor.fetchone().keys()
for column in columns:
    cursor.execute("update data set " + column + " = NULL where " 
               + column + "= '';")
db.commit()
