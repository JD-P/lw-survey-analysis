import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("infile", help="The filepath to read columns from.")
arguments = parser.parse_args()

infile = open(arguments.infile)
contents = infile.read()
diffables = contents.split("----")

def diff_diffable(diffable):
    """Take in a diffable consisting of two columns of values from the 
    2016 and 2014 surveys and figure out the difference between the two, returns
    the printable representation of the diff."""
    (d2016, d2014) = diffable.split("\n\n")
    labels = [line.split(":")[0] for line in d2016.split("\n") if line]
    c2016 = [float(line.split(":")[1].strip().split()[1]) 
             for line in d2016.split("\n") if line]
    c2014 = [float(line.split(":")[1].strip().split()[1][:-1]) / 100 
             for line in d2014.split("\n") if line]
    diff_nums = (np.array(c2016) - np.array(c2014)) * 100
    totals = [line.split(":")[1].strip().split()[0] 
              for line in d2016.split("\n") if line]
    percentages = [("%.3f" % 
                   (float(line.split(":")[1].strip().split()[1]) * 100)) + "%"
                   for line in d2016.split("\n") if line]
    conv = lambda s: "+" + s + "%" if float(s) > 0 else s + "%"
    diff_num_strs = [conv("%.3f" % num) for num in diff_nums]
    outline_nums = [' '.join([str(value) for value in outline]) 
                    for outline in tuple(zip(diff_num_strs, totals, percentages))]
    outlines = [': '.join(outline) + "  " for outline in zip(labels, outline_nums)]
    return '\n'.join(outlines)

[print(diff_diffable(diffable), end="\n\n") for diffable in diffables]  
