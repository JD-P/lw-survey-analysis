import sqlite3
import statistics
from libsurveyanalysis import SurveyStructure
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("structure", help="Filepath to the survey structure.")
parser.add_argument("database", help="The sqlite3 database containing the results.")
arguments = parser.parse_args()

structure = SurveyStructure(arguments.structure)
db_conn = sqlite3.connect(arguments.database)
cursor = db_conn.cursor()
groups = structure.groups()

conditions = {
    "Age":"where Age <= 122",
    "IQ":"where 65 < IQ AND IQ < 250",
    "SAT":"where SAT <= 1600 AND SAT > 0",
    "SAT2":"where SAT2 <= 2400 AND SAT2 > 0",
    "ACT":"where ACT <= 36"}

for group_tuple in groups:
    (group_name, keys) = group_tuple
    print(group_name)
    end = "\n\t"
    for key in keys:
        question_data = structure[key]
        if question_data["label"]:
            print(question_data["label"] + ":", end=end)
        else:
            print(key + ":", end=end)
        end = "\n\t\t"
        if question_data["dtype"] == "N":
            if key in conditions:
                condition = conditions[key]
                cursor.execute("select " + key + " from data " + condition + ";")
            else:
                cursor.execute("select " + key + " from data;")
            data_wrapped = cursor.fetchall()
            data = [float(value[0]) for value in data_wrapped if value[0]]
            print("Mean:", statistics.mean(data), end=end)
            print("Median:", statistics.median(data), end=end)
            try:
                print("Mode:", statistics.mode(data), end=end)
            except statistics.StatisticsError:
                print("Mode:", "All values found equally likely.")
        print(end="\n\t")
