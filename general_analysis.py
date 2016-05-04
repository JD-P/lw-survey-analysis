import sqlite3
import statistics
from libsurveyanalysis import SurveyStructure
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("structure", help="Filepath to the survey structure.")
parser.add_argument("database", help="The sqlite3 database containing the results.")
parser.add_argument("-n", "--no-null", action="store_true", dest="no_null", 
                    help="Only calculate results on each question for those who "
                    + "answered it.")
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

def count_answers(rows, question_data, cursor, no_null=False):
    """Count the distinct answers in the given rows and return a count and 
    fraction for each answer. 

    no_null - Determines whether to count non-answers in the polling or not."""
    answers = question_data["answers"]
    answer_labels = []
    for answer in answers:
        answer_labels.append(answer["label"])
    answers_dict = {}.fromkeys(answer_labels)
    if no_null:
        data = [value[0] for value in rows if value[0] and value[0] != "N/A"]
        for answer in answer_labels:
            count = data.count(answer)
            fraction = round(data.count(answer) / len(data), 3)
            answers_dict[answer] = (count, fraction)
    else:
        data = [value[0] for value in rows]
        for answer in answer_labels:
            count = data.count(answer)
            fraction = round(data.count(answer) / len(data), 3)
            answers_dict[answer] = (count, fraction)
        if data.count("N/A") > 0:
            count = data.count("N/A")
            fraction = round(data.count("N/A") / len(data), 3)
            answers_dict["N/A"] = (count, fraction)
        else:
            count = data.count(None)
            fraction = round(data.count(None) / len(data), 3)
            answers_dict[None] = (count, fraction)
    if len(question_data["sub_questions"]) > 1:
        raise ValueError("Received more than one subquestion when counting 'L'" + 
                         " type question.")
    elif len(question_data["sub_questions"]) == 1:
        for subquestion in question_data["sub_questions"]:
            cursor.execute("select count(" + question_data["code"] + 
                           "_" + subquestion["code"] + ") from data;")
            count = cursor.fetchone()[0]
            if arguments.no_null:
                data = [value[0] for value in rows if value[0] 
                        and value[0] != "N/A"]
                fraction = count / len(data)
            else:
                fraction = count / len(rows)
        answers_dict[subquestion["label"]] = (count, fraction)
    return answers_dict

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
            # Numeric question. eg. Age.
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
                print("Mode:", "All values found equally likely.", end=end)
        elif question_data["dtype"] == "Y":
            # Binary Question
            answers = ("Yes", "No")
            cursor.execute("select " + key + " from data;")
            question_rows = cursor.fetchall()
            if arguments.no_null:
                data = [value[0] for value in question_rows if value[0] and 
                        value[0] != "N/A"]
                for answer in answers:
                    print(answer + ":", 
                          data.count(answer), 
                          round(data.count(answer) / len(data), 3), 
                          end=end)
            else:
                data = [value[0] for value in question_rows]
                for answer in answers:
                    print(answer + ":", 
                          data.count(answer),
                          round(data.count(answer) / len(data), 3),
                          end=end)
                print("N/A:",
                      data.count("N/A"),
                      round(data.count("N/A") / len(data), 3),
                      end=end)
        elif question_data["dtype"] == "L":
            # Radio button
            answers = question_data["answers"]
            cursor.execute("select " + key + " from data;")
            question_rows = cursor.fetchall()
            if arguments.no_null:
                answer_counts = count_answers(question_rows, question_data, 
                                              cursor, True)
                for answer in answers:
                    (count, fraction) = answer_counts[answer["label"]]
                    print(answer["label"] + ":", count, fraction, end=end)
                for subquestion in question_data["sub_questions"]:
                    (count, fraction) = answer_counts[subquestion["label"]]
                    print(subquestion["label"] + ":", count, fraction, end=end)
            else:
                answer_counts = count_answers(question_rows, question_data, cursor)
                for answer in answers:
                    (count, fraction) = answer_counts[answer["label"]]
                    print(answer["label"] + ":", count, fraction, end=end)
                for subquestion in question_data["sub_questions"]:
                    (count, fraction) = answer_counts[subquestion["label"]]
                    print(subquestion["label"] + ":", count, fraction, end=end)
                if "N/A" in answer_counts:
                    (count, fraction) = answer_counts["N/A"]
                    print("N/A:", count, fraction, end=end)
                else:
                    (count, fraction) = answer_counts[None]
                    print("None:", count, fraction, end=end)
        elif question_data["dtype"] == "M":
            # Multiple choice with checkbox/binary answers
            for subquestion in question_data["sub_questions"]:
                print(subquestion["label"] + ":", end=end)
                code = question_data["code"] + "_" + subquestion["code"]
                cursor.execute("select " + code + " from data;")
                subquestion_rows = cursor.fetchall()
                if arguments.no_null:
                    data = [value[0] for value in subquestion_rows if value[0]]
                    (count1, fraction1, count2, fraction2) = (
                        data.count("Yes"),
                        data.count("Yes") / len(data),
                        data.count("No"),
                        data.count("No") / len(data))
                    print("Yes:", count1, fraction1, end=end)
                    print("No:", count2, fraction2, end=end)
                else:
                    data = [value[0] for value in subquestion_rows]
                    (count1, fraction1, 
                     count2, fraction2,
                     count3, fraction3) = (
                         data.count("Yes"),
                         data.count("Yes") / len(data),
                         data.count("No"),
                         data.count("No") / len(data),
                         data.count("N/A"),
                         data.count("N/A") / len(data))
                    print("Yes:", count1, fraction1, end=end)
                    print("No:", count2, fraction2, end=end)
                    print("N/A:", count3, fraction3, end=end)
        elif question_data["dtype"] == "F":
            # Multiple choice with multiple answers
            for subquestion in question_data["sub_questions"]:
                print(subquestion["label"] + ":", end=end)
                answers = question_data["answers"]
                code = question_data["code"] + "_" + subquestion["code"]
                cursor.execute("select " + code + " from data;")
                subquestion_rows = cursor.fetchall()
                if arguments.no_null:
                    data = [value[0] for value in subquestion_rows if value[0]]
                    for answer in answers:
                        (count, fraction) = (
                            data.count(answer["label"]),
                            data.count(answer["label"]) / len(data)
                        )
                        print(answer["label"] + ":", count, fraction, end=end)
                else:
                    data = [value[0] for value in subquestion_rows]
                    for answer in answers:
                        (count, fraction) = (
                            data.count(answer["label"]),
                            data.count(answer["label"]) / len(data)
                        )
                        print(answer["label"] + ":", count, fraction, end=end)
                    if "N/A" in data:
                        (count, fraction) = (
                            data.count("N/A"),
                            data.count("N/A") / len(data)
                        )
                        print("N/A:", count, fraction, end=end)
                    else:
                        (count, fraction) = (
                            data.count(None),
                            data.count(None) / len(data)
                        )
                        print("None:", count, fraction, end=end)
        elif question_data["dtype"] == "!":
            # Drop down list datatype
            answers = question_data["answers"]
            cursor.execute("select " + question_data["code"] + " from data;")
            question_rows = cursor.fetchall()
            print(question_data["label"] + ":", end=end)
            if arguments.no_null:
                data = [value[0] for value in question_rows if value[0]]
                for answer in answers:
                    (count, fraction) = (data.count(answer["label"]),
                                         data.count(answer["label"]) / len(data))
                    print(answer["label"] + ":", count, fraction, end=end)
            else:
                answer_counts = count_answers(question_rows, 
                                               question_data, cursor)
                for answer in answers:
                    (count, fraction) = answer_counts[answer["label"]]
                    print(answer["label"] + ":", count, fraction, end=end)
                if "N/A" in answer_counts:
                    (count, fraction) = answer_counts["N/A"]
                    print("N/A:", count, fraction, end=end)
                else:
                    (count, fraction) = answer_counts[None]
                    print("None:", count, fraction, end=end)
        elif question_data["dtype"] == "K":
            # Multiple numeric questions. eg. Charity section.
            print(question_data["label"] + ":", end=end)
            for subquestion in question_data["sub_questions"]:
                print(subquestion["label"] + ":", end=end)
                code = question_data["code"] + "_" + subquestion["code"]
                cursor.execute("select " + code + " from data;")
                subquestion_rows = cursor.fetchall()
                data = [value[0] for value in subquestion_rows if value[0]]
                print("Mean:", statistics.mean(data), end=end)
                print("Median:", statistics.median(data), end=end)
                try:
                    print("Mode:", statistics.mode(data), end=end)
                except statistics.StatisticsError:
                    print("Mode:", "All values found equally likely.", end=end)
        print(end="\n\t")
