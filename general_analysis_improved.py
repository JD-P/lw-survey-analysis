import re
import sqlite3
import libsurveyanalysis as lsa
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("structure", help="Filepath to the survey structure.")
parser.add_argument("database", help="The sqlite3 database containing the results.")
parser.add_argument("-n", "--no-null", action="store_true", dest="no_null", 
                    help="Only calculate results on each question for those who "
                    + "answered it.")
parser.add_argument("-f", "--filter", action="store_true",
                    help="Filter out respondents with outlier answers.")
arguments = parser.parse_args()

structure = lsa.SurveyStructure(arguments.structure)
db_conn = sqlite3.connect(arguments.database)
cursor = db_conn.cursor()
groups = structure.groups()
keys = sum([group[1] for group in groups], [])
view = "data"

conditions = (["((age > 0 AND age <= 122) OR (age IS NULL) OR (age = 'N/A'))",
               "((65 < IQ AND IQ < 250) OR (IQ IS NULL) OR (IQ = 'N/A'))",
               "((SAT <= 1600 AND SAT > 0) OR (SAT IS NULL) OR (SAT ='N/A'))",
               "((SAT2 <= 2400 AND SAT2 > 0) OR (SAT2 IS NULL) OR (SAT2 = 'N/A'))",
               "((ACT <= 36 AND ACT > 0) OR (ACT IS NULL) OR (ACT = 'N/A'))"] + 
              ["((ProbabilityQuestions_{} >=0 ".format(str(i + 1)) +
               "AND ProbabilityQuestions_{} <= 100)".format(str(i + 1)) +
               " OR (ProbabilityQuestions_{} IS NULL)".format(str(i + 1)) + 
               " OR (ProbabilityQuestions_{} = 'N/A'))".format(str(i + 1))
               for i in range(12)])
    
if arguments.filter:
    cursor.execute("CREATE TEMP VIEW filtered AS select * from data where " +
                   ' AND '.join(conditions) + ";")
    view = "filtered"
if arguments.no_null:
    output = lsa.analyze_keys(keys, db_conn, structure, {}, view, no_null=True)
else:
    output = lsa.analyze_keys(keys, db_conn, structure, {}, view)

def replace(num_match):
    num_string = num_match.group()
    return " " + str(round(float(num_string) * 100, 3)) + "%\n"

cursor.execute("select count(*) from data;")
total_respondents = cursor.fetchone()[0]
cursor.execute("select count(*) from " + view + ";")
sample_size = cursor.fetchone()[0]
print("Total survey respondents:", total_respondents)
print("Respondent surveys used:", sample_size, end="\n\n")

output = re.sub(" (0\.[0-9]+)\n| (0\.[0-9]+)\n", 
                replace, output)

print(output)
