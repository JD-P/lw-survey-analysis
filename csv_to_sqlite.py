# made and placed in the public domain by Bartosz Wróblewski, sometimes known as bawr

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
    return ("" != c.strip())
     
def numeric(c):
    try:
        i = float(c)
    except ValueError:
        t = False
    else:
        t = True
    return t
     
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
