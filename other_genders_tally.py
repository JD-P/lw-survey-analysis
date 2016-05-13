import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="The filepath to the genders file to analyze.")
parser.add_argument("-e", "--esoteric", action="store_true",
                    help="Print esoteric answers.")
arguments = parser.parse_args()

infile = open(arguments.filepath)
contents = infile.read()
lines = contents.split("\n")
values = [line.split("|")[1].strip() for line in lines if line.strip()]
print("Sample Size:", len(values))
for value in sorted(list(set(values))):
    print(value, values.count(value))

if arguments.esoteric:
    print(end="\n")
    esoteric = [line.split("|")[0] for line in lines if line.strip() and 
                line.split("|")[1].strip() == "E"]
    for answer in esoteric:
        print(answer)
