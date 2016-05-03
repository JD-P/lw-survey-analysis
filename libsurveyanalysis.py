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

    def groups(self):
        """Return the groups in this SurveyStructure."""
        return self._groups
