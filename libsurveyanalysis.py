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
                    if question_data["sub_questions"][0]["code"] == "other":
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
                    if question_data["sub_questions"][0]["code"] == "other":
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

class KeyAnalyzer:
    def __init__(self, connection, structure, conditions, view, no_null=False):
        self._connection = connection
        self._structure = structure
        self._conditions = conditions
        self._view = view
        self._no_null = no_null
        
    def analyze_key(key):
        """The core of general_analysis.py packed into a reusable function. Returns
        the printable representation of the key analysis.

        key - The key to analyze.
        connection - The database connection to pull rows from.
        structure - The survey structure file to use."""
        cursor = self._connection.cursor()
        question_data = self._structure[key]
        result = {}
        if question_data["dtype"] == "!":
            analyzer = getattr(self, "_analyze_exclamation")
        else:
            analyzer = getattr(self, "_analyze_" + question_data["dtype"])
        if key in self._conditions:
            condition = self._conditions[key]
        return analyzer(key, self._view, condition, cursor)
    
    def _analyze_N(self, key, view, question_data, cursor, condition=False,
                   no_null=False):
        """Analyze a numeric question. eg. Age."""
        if condition:
            cursor.execute("select " + key + " from " + view  + " " + condition + ";")
        else:
            cursor.execute("select " + key + " from " + view + ";")
        data_wrapped = cursor.fetchall()
        data = [float(value[0]) for value in data_wrapped if value[0]]
        result = {}
        result["sum"] = sum(data)
        try:
            result["mean"] = statistics.mean(data)
        except statistics.StatisticsError:
            result["mean"] = None
        try:
            result["median"] = statistics.median(data)
        except statistics.StatisticsError:
            result["median"] = None
        try:
            result["mode"] = statistics.mode(data)
        except statistics.StatisticsError:
            result["mode"] = None
        try:
            result["stdev"] = statistics.stdev(data)
        except statistics.StatisticsError:
            result["stdev"] = None
        return result
            
    def _analyze_Y(self, key, view, question_data, cursor, condition=False,
                   no_null=False):
        """Analyze a binary yes or no question."""
        answers = ("Yes", "No")
        cursor.execute("select " + key + " from " + view + ";")
        question_rows = cursor.fetchall()
        result = {}
        if no_null:
            data = [value[0] for value in question_rows if value[0] and 
                    value[0] != "N/A"]
            for answer in answers:
                result[answer + "_count"] = data.count(answer)
                result[answer + "_fraction"] = data.count(answer) / len(data)
        else:
            data = [value[0] for value in question_rows]
            for answer in answers:
                result[answer + "_count"] = data.count(answer)
                result[answer + "_fraction"] = data.count(answer) / len(data)
            result["N/A_count"] = data.count("N/A") 
            result["N/A_fraction"] = data.count("N/A") / len(data)
        return result
    
    def _analyze_L(self, key, view, question_data, cursor, condition=False,
                   no_null=False):
        """Analyze a radio button question. (I.E, a list of predetermined answers."""
        answers = question_data["answers"]
        cursor.execute("select " + key + " from " + view + ";")
        question_rows = cursor.fetchall()
        if no_null:
            answer_counts = _count_answers(question_rows, question_data,
                                           cursor, view, no_null=True)
        else:
            answer_counts = _count_answers(question_rows, question_data,
                                           cursor, view)
        for answer in answers:
            (count, fraction) = answer_counts[answer["label"]]
            result[answer["label"] + "_count"] = count
            result[answer["label"] + "_fraction"] = fraction

        # We only expect to ever see "other" as a subquestion for radio button lists
        # TODO: This will break if I ever encounter a radio list answer named 'other'
        # (But it'll be too onerous to fix it right this minute...)
        result["sub_questions"] = []
        sub_result = {}
        # TOTEST: Make sure that this is in fact the right key
        (count, fraction) = answer_counts["Other"]
        sub_result["count"] = count 
        sub_result["fraction"] = fraction
        result["sub_questions"].append(sub_result)
        
        if "N/A" in answer_counts:
            (count, fraction) = answer_counts["N/A"]
            result["N/A_count"] = count
            result["N/A_fraction"] = fraction
        elif None in answer_counts:
            (count, fraction) = answer_counts[None]
            result["None_count"] = count 
            result["None_fraction"] = fraction
        return result
    
    def _analyze_M(self, key, view, question_data, cursor, condition=False,
                   no_null=False):
        """Analyze multiple choice question with checkbox/binary answers."""
        result["sub_questions"] = []
        for subquestion in question_data["sub_questions"]:
            sub_result = {}
            code = question_data["code"] + "_" + subquestion["code"]
            cursor.execute("select " + code + " from " + view + ";")
            subquestion_rows = cursor.fetchall()
            if no_null:
                data = [value[0] for value in subquestion_rows if value[0]]
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
            sub_result["yes_count"] = count1 
            sub_result["yes_fraction"] = fraction1
            sub_result["no_count"] = count2
            sub_result["no_fraction"] = fraction2
            sub_result["na_count"] = count3
            sub_result["na_fraction"] = fraction3
            result["sub_questions"].append(sub_result)
        return result
                
    def _analyze_F(self, key, view, question_data, cursor, condition=False,
                   no_null=False):
        """Analyze multiple choice question with multiple answers."""
        result["sub_questions"] = []
        for subquestion in question_data["sub_questions"]:
            sub_result = {}
            answers = question_data["answers"]
            code = question_data["code"] + "_" + subquestion["code"]
            cursor.execute("select " + code + " from " + view + ";")
            subquestion_rows = cursor.fetchall()
            if no_null:
                data = [value[0] for value in subquestion_rows if value[0]]
            else:
                data = [value[0] for value in subquestion_rows]
            for answer in answers:
                (count, fraction) = (
                    data.count(answer["label"]),
                    data.count(answer["label"]) / len(data)
                )
                sub_result[answer["label"] + "_count"] = count
                sub_result[answer["label"] + "_fraction"] = fraction
            if "N/A" in data:
                (count, fraction) = (
                    data.count("N/A"),
                    data.count("N/A") / len(data)
                )
                sub_result["N/A_count"] = count
                sub_result["N/A_fraction"] = fraction
            elif None in data:
                    (count, fraction) = (
                        data.count(None),
                        data.count(None) / len(data)
                    )
                    sub_result["None_count"] = count
                    sub_result["None_fraction"] = fraction
                           
    def _analyze_exclamation(self, key, view, question_data, cursor, condition=False,
                             no_null=False):
        """Analyze drop down list question."""
        result = {}
        answers = question_data["answers"]
        cursor.execute("select " + question_data["code"] + " from " + view + ";")
        question_rows = cursor.fetchall()
        if no_null:
            answer_counts = _count_answers(question_rows,
                                           question_data, cursor, view, no_null)
        else:
            answer_counts = _count_answers(question_rows, 
                                           question_data, cursor, view)
            for answer in answers:
                (count, fraction) = answer_counts[answer["label"]]
                result[answer["label"] + "_count"] = count
                result[answer["label"] + "_fraction"] = fraction
            if "N/A" in answer_counts:
                (count, fraction) = answer_counts["N/A"]
                result["N/A_count"] = count
                result["N/A_fraction"] = fraction
            elif None in answer_counts:
                (count, fraction) = answer_counts[None]
                result["None_count"] = count
                result["None_fraction"] = fraction
                           
    def _analyze_K(self, key, view, question_data, cursor, condition=False,
                   no_null=False):
        """Analyze multiple numeric questions. eg. Charity section."""
        result = {}
        result["sub_questions"] = []
        for subquestion in question_data["sub_questions"]:
            sub_result = {}
            code = question_data["code"] + "_" + subquestion["code"]
            cursor.execute("select " + code + " from " + view + ";")
            subquestion_rows = cursor.fetchall()
            data = [value[0] for value in subquestion_rows if value[0]]
            sub_result["sum"] = sum(data)
            try:
                sub_result["mean"] = statistics.mean(data)
            except statistics.StatisticsError:
                sub_result["mean"] = None
            try:
                sub_result["median"] = statistics.median(data)
            except statistics.StatisticsError:
                sub_result["median"] = None
            try:
                sub_result["mode"] = statistics.mode(data)
            except statistics.StatisticsError:
                sub_result["mode"] = None
            try:
                sub_result["stdev"] = statistics.stdev(data)
            except statistics.StatisticsError:
                sub_result["stdev"] = None
            result["sub_questions"].append(sub_result)
        return result
                           
    def _analyze_5(self, key, view, question_data, cursor, condition=False,
                   no_null=False):
        """Analyze five point rating scale question."""
        result = {}
        answers = (1, 2, 3, 4, 5)
        code = question_data["code"]
        cursor.execute("select " + code + " from " + view + ";")
        question_rows = cursor.fetchall()
        data = [value[0] for value in question_rows]
        for answer in answers:
            (count, fraction) = (data.count(answer), 
                                 data.count(answer) / len(data))
            result[str(answer) + "_count"] = count
            result[str(answer) + "_fraction"] = fraction
            
        (count, fraction) = (data.count(None),
                             data.count(None) / len(data))
        result["None_count"] = count
        result["None_fraction"] = fraction

def analyze_keys(keys, connection, structure, conditions, view, no_null=False):
    """Analyze a set of keys and return the printable representation of the 
    analysis.

    keys - An iterable containing the keys. It should be noted that survey 
    structure keys do not contain subquestions. So instead of ExampleKey[4] 
    you would just give "ExampleKey" and let the analysis program handle 
    subquestions. You can get a list of such keys using the .keys() call of a 
    survey structure object.

    This function returns a report object. The report object is a dictionary 
    which contains all the keys analyzed by analyze_keys as an intermediate format
    that can be easily traversed and then formatted into whatever output format
    the calling program would like.

    Since the dictionary is unordered, the order of keys to print in is taken from
    the survey structure object described above. You would call .groups() or .keys()
    on the survey structure, and then use that ordered list to determine which keys
    in the report to print in which order."""
    report = {}.fromkeys(structure.keys())
    key_analyzer = KeyAnalyzer(connection, structure, conditions, view, no_null)
    for group in structure.groups():
        group_keys = group[1]
        for key in group_keys:
            if key in keys:
                report[key] = key_analyzer.analyze_key(key)
    return report
