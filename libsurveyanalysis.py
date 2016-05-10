import statistics
import sqlite3
import csv
import re

class SurveyStructure:
    """Represents the structure of the survey, allowing analysis to know the 
    order of answers to questions and the data type of the question being asked.
    Along with the full question along with its code, etc."""
    def __init__(self, filepath, sql=False):
        """Takes a filepath to the survey structure and imports it into this
        data structure."""
        html_strip = re.compile("\t(<*>)")
        with open(filepath) as infile:
            structure_txt = infile.read()
            self._structure = {}
            rows = structure_txt.split("\n")
            groups = []
            group_indice = -1
            questions = []
            question_indice = -1
            for row in rows:
                row = html_strip.sub(" \g<1>", row)
                values = row.split("\t")
                row_type = values[0]
                if row_type.upper() == "G":
                    group_name = values[2]
                    group_indice += 1
                    groups.append((group_name, []))
                elif row_type.upper() == "Q":
                    code = values[2]
                    question_indice += 1
                    questions.append([])
                    questions[question_indice].append(("Q",row))
                    groups[group_indice][1].append(code)
                elif row_type.upper() == "SQ":
                    questions[question_indice].append(("SQ", row))
                elif row_type.upper() == "A":
                    questions[question_indice].append(("A", row))
                else:
                    continue
        self._groups = groups
        self._questions = {}
        for question_set in questions:
            answers = []
            sub_questions = []
            for question_tuple in question_set:
                values = question_tuple[1].split("\t")
                if question_tuple[0] == "Q":
                    data_type = values[1]
                    code = values[2]
                    unknown = values[3]
                    label = values[4]
                    question_data = (data_type, code, label)
                elif question_tuple[0] == "A":
                    data_type = values[1]
                    code = values[2]
                    label = values[4]
                    answers.append({"dtype":data_type,
                                    "code":code,
                                    "label":label})
                elif question_tuple[0] == "SQ":
                    data_type = values[1]
                    code = values[2]
                    unknown = values[3]
                    label = values[4]
                    sub_questions.append({"dtype":data_type,
                                          "code":code,
                                          "unknown":unknown,
                                          "label":label})
                else:
                    raise ValueError("Row type " + 
                                     question_tuple[0] + 
                                     " found in question set.")
            self._questions[question_data[1]] = {"dtype":question_data[0],
                                                 "code":question_data[1],
                                                 "label":question_data[2],
                                                 "answers":answers,
                                                 "sub_questions":sub_questions}
                                                 
    def __getitem__(self, key):
        return self._questions[key]

    def keys(self):
        """Return the keys in this SurveyStructure."""
        keys = []
        for group in self._groups:
            keys += group[1]
        return keys

    def csv_keys(self):
        """Return the keys that will be found in the CSV files."""
        keys = []
        for group in self._groups:
            for key_base in group[1]:
                question_data = self[key_base]
                if question_data["sub_questions"]:
                    if len(question_data["sub_questions"]) == 1:
                        keys.append(question_data["code"])
                        for subquestion in question_data["sub_questions"]:
                            keys.append(question_data["code"] + "[" 
                                        + subquestion["code"] + "]")
                    else:
                        for subquestion in question_data["sub_questions"]:
                            keys.append(question_data["code"] + "["
                                        + subquestion["code"] + "]")
                else:
                    keys.append(question_data["code"])
        return keys

    def sql_keys(self):
        """Return the keys that will be found in the sqlite files."""
        keys = []
        for group in self._groups:
            for key_base in group[1]:
                question_data = self[key_base]
                if question_data["sub_questions"]:
                    if len(question_data["sub_questions"]) == 1:
                        keys.append(question_data["code"])
                        for subquestion in question_data["sub_questions"]:
                            keys.append(question_data["code"] + "_" 
                                        + subquestion["code"])
                    else:
                        for subquestion in question_data["sub_questions"]:
                            keys.append(question_data["code"] + "_"
                                        + subquestion["code"])
                else:
                    keys.append(question_data["code"])
        return keys

    def groups(self):
        """Return the groups in this SurveyStructure."""
        return self._groups

def val_prob_ans(answer):
    """Validate whether an answer to a probability question is legitimate or not."""
    validator = re.compile("delta|epsilon|[0-9]*\.[0-9]+|[0-9]+")
    try:
        valid = validator.search(answer)
    except TypeError:
        if answer == None:
            return False
    if valid:
        answer_string = answer[valid.start():valid.end()]
        if answer_string == "delta":
            answer_string = "99." + "9" * 50
        elif answer_string == "epsilon":
            answer_string = "0." + ("0" * 49) + "1"
        return float(answer_string)
    else:
        return False

def _count_answers(rows, question_data, cursor, view, no_null=False):
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
                           "_" + subquestion["code"] + ") from " + view + ";")
            count = cursor.fetchone()[0]
            if no_null:
                data = [value[0] for value in rows if value[0] 
                        and value[0] != "N/A"]
                fraction = count / len(data)
            else:
                fraction = count / len(rows)
        answers_dict[subquestion["label"]] = (count, fraction)
    return answers_dict

def analyze_key(key, connection, structure, conditions, view, no_null=False):
    """The core of general_analysis.py packed into a reusable function. Returns
    the printable representation of the key analysis.

    key - The key to analyze.
    connection - The database connection to pull rows from.
    structure - The survey structure file to use."""
    key_printout = ""
    cursor = connection.cursor()
    question_data = structure[key]
    end = "\n\t"
    if question_data["label"]:
        key_printout +=(question_data["label"] + ":" + end)
    else:
        key_printout +=(key + ":" + end)
    end = "\n\t\t"
    if question_data["dtype"] == "N":
        # Numeric question. eg. Age.
        if key in conditions:
            condition = conditions[key]
            cursor.execute("select " + key + " from " + view  + " " + condition + ";")
        else:
            cursor.execute("select " + key + " from " + view + ";")
        data_wrapped = cursor.fetchall()
        data = [float(value[0]) for value in data_wrapped if value[0]]

        key_printout +=("Sum:" + str(sum(data)) + end)
        try:
            key_printout +=("Mean:" + str(statistics.mean(data)) + end)
        except statistics.StatisticsError:
            key_printout +=("Mean: No datapoints in set.")
        try:
            key_printout +=("Median:" + str(statistics.median(data)) + end)
        except statistics.StatisticsError:
            key_printout +=("Median: No datapoints in set.")
        try:
            key_printout +=("Mode:" + str(statistics.mode(data)) + end)
        except statistics.StatisticsError:
            key_printout +=("Mode:" + "All values found equally likely." + end)
    elif question_data["dtype"] == "Y":
        # Binary Question
        answers = ("Yes", "No")
        cursor.execute("select " + key + " from " + view + ";")
        question_rows = cursor.fetchall()
        if no_null:
            data = [value[0] for value in question_rows if value[0] and 
                    value[0] != "N/A"]
            for answer in answers:
                key_printout +=(answer + ":" +
                      str(data.count(answer)) + " " + 
                      str(round(data.count(answer) / len(data), 3))
                      + end)
        else:
            data = [value[0] for value in question_rows]
            for answer in answers:
                key_printout +=(answer + ":" +
                      str(data.count(answer)) + " " + 
                      str(round(data.count(answer) / len(data), 3))
                      + end)
            key_printout +=("N/A:" +
                  str(data.count("N/A")) + " " + 
                  str(round(data.count("N/A") / len(data), 3))
                  + end)
    elif question_data["dtype"] == "L":
        # Radio button
        answers = question_data["answers"]
        cursor.execute("select " + key + " from " + view + ";")
        question_rows = cursor.fetchall()
        if no_null:
            answer_counts = _count_answers(question_rows, question_data, 
                                          cursor, view, True)
            for answer in answers:
                (count, fraction) = answer_counts[answer["label"]]
                key_printout += (answer["label"] + ":" + str(count) + " " + str(fraction) + end)
            for subquestion in question_data["sub_questions"]:
                (count, fraction) = answer_counts[subquestion["label"]]
                key_printout += (subquestion["label"] + ":" + str(count) + " " + str(fraction) + end)
        else:
            answer_counts = _count_answers(question_rows, question_data, cursor, view)
            for answer in answers:
                (count, fraction) = answer_counts[answer["label"]]
                key_printout += (answer["label"] + ":" + str(count) + " " + str(fraction) + end)
            for subquestion in question_data["sub_questions"]:
                (count, fraction) = answer_counts[subquestion["label"]]
                key_printout += (subquestion["label"] + ":" + str(count) + " " + str(fraction) + end)
            if "N/A" in answer_counts:
                (count, fraction) = answer_counts["N/A"]
                key_printout +=("N/A:" + str(count) + " " + str(fraction) + end)
            else:
                (count, fraction) = answer_counts[None]
                key_printout +=("None:" + str(count) + " " + str(fraction) + end)
    elif question_data["dtype"] == "M":
        # Multiple choice with checkbox/binary answers
        for subquestion in question_data["sub_questions"]:
            key_printout += (subquestion["label"] + ":" + end)
            code = question_data["code"] + "_" + subquestion["code"]
            cursor.execute("select " + code + " from " + view + ";")
            subquestion_rows = cursor.fetchall()
            if no_null:
                data = [value[0] for value in subquestion_rows if value[0]]
                (count1, fraction1, count2, fraction2) = (
                    data.count("Yes"),
                    data.count("Yes") / len(data),
                    data.count("No"),
                    data.count("No") / len(data))
                key_printout +=("Yes:" + str(count1) + " " + str(fraction1) + end)
                key_printout +=("No:" + str(count2) + " " + str(fraction2) + end)
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
                key_printout +=("Yes:" + str(count1) +  " " + str(fraction1) + end)
                key_printout +=("No:" + str(count2) + " " + str(fraction2) + end)
                key_printout +=("N/A:" + str(count3) + " " + str(fraction3) + end)
    elif question_data["dtype"] == "F":
        # Multiple choice with multiple answers
        for subquestion in question_data["sub_questions"]:
            key_printout += (subquestion["label"] + ":" + end)
            answers = question_data["answers"]
            code = question_data["code"] + "_" + subquestion["code"]
            cursor.execute("select " + code + " from " + view + ";")
            subquestion_rows = cursor.fetchall()
            if no_null:
                data = [value[0] for value in subquestion_rows if value[0]]
                for answer in answers:
                    (count, fraction) = (
                        data.count(answer["label"]),
                        data.count(answer["label"]) / len(data)
                    )
                    key_printout += (answer["label"] + ":" + str(count) + " " + str(fraction) + end)
            else:
                data = [value[0] for value in subquestion_rows]
                for answer in answers:
                    (count, fraction) = (
                        data.count(answer["label"]),
                        data.count(answer["label"]) / len(data)
                    )
                    key_printout += (answer["label"] + ":" + str(count) + " " + str(fraction) + end)
                if "N/A" in data:
                    (count, fraction) = (
                        data.count("N/A"),
                        data.count("N/A") / len(data)
                    )
                    key_printout += ("N/A:" + str(count) + " " + str(fraction) + end)
                else:
                    (count, fraction) = (
                        data.count(None),
                        data.count(None) / len(data)
                    )
                    key_printout += ("None:" + str(count) + " " + str(fraction) + end)
    elif question_data["dtype"] == "!":
        # Drop down list datatype
        answers = question_data["answers"]
        cursor.execute("select " + question_data["code"] + " from " + view + ";")
        question_rows = cursor.fetchall()
        key_printout += (question_data["label"] + ":" + end)
        if no_null:
            data = [value[0] for value in question_rows if value[0]]
            for answer in answers:
                (count, fraction) = (data.count(answer["label"]),
                                     data.count(answer["label"]) / len(data))
                key_printout +=(answer["label"] + ":" + str(count) + " " + str(fraction) + end)
        else:
            answer_counts = _count_answers(question_rows, 
                                           question_data, cursor, view)
            for answer in answers:
                (count, fraction) = answer_counts[answer["label"]]
                key_printout +=(answer["label"] + ":" + str(count) + " " + str(fraction) + end)
            if "N/A" in answer_counts:
                (count, fraction) = answer_counts["N/A"]
                key_printout +=("N/A:" + str(count) + " " + str(fraction) + end)
            else:
                (count, fraction) = answer_counts[None]
                key_printout +=("None:" + str(count) + " " + str(fraction) + end)
    elif question_data["dtype"] == "K":
        # Multiple numeric questions. eg. Charity section.
        key_printout +=(question_data["label"] + ":" + end)
        for subquestion in question_data["sub_questions"]:
            key_printout +=(subquestion["label"] + ":" + end)
            code = question_data["code"] + "_" + subquestion["code"]
            cursor.execute("select " + code + " from " + view + ";")
            subquestion_rows = cursor.fetchall()
            data = [value[0] for value in subquestion_rows if value[0]]
            key_printout +=("Sum:" + str(sum(data)) + end)
            try:
                key_printout +=("Mean:" + str(statistics.mean(data)) + end)
            except statistics.StatisticsError:
                key_printout +=("Mean: No datapoints in set.")
            try:
                key_printout +=("Median:"+ str(statistics.median(data)) + end)
            except statistics.StatisticsError:
                key_printout +=("Mode: No datapoints in set.")
            try:
                key_printout +=("Mode:" + str(statistics.mode(data)) + end)
            except statistics.StatisticsError:
                key_printout +=("Mode:" + "All values found equally likely." + end)
    key_printout += "\n\t"
    return key_printout

def analyze_keys(keys, connection, structure, conditions, view, no_null=False):
    """Analyze a set of keys and return the printable representation of the 
    analysis.

    keys - An iterable containing the keys. It should be noted that survey 
    structure keys do not contain subquestions. So instead of ExampleKey[4] 
    you would just give "ExampleKey" and let the analysis program handle 
    subquestions. You can get a list of such keys using the .keys() call of a 
    survey structure object."""
    full_printout = ""
    for group in structure.groups():
        group_keys = group[1]
        for key in group_keys:
            if key in keys:
                full_printout += analyze_key(key, connection, structure, 
                                             conditions, view, no_null=no_null)
    return full_printout
