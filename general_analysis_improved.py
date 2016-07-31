import re
import sqlite3
from bs4 import BeautifulSoup
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
    report = lsa.analyze_keys(keys, db_conn, structure, {}, view, no_null=True)
else:
    report = lsa.analyze_keys(keys, db_conn, structure, {}, view)

class KeyFormatter:
    def __init__(self, report, structure):
        self._report = report
        self._structure = structure

    def format_keys(self):
        """Takes a report object as generated by lsa.analyze_keys and formats it for 
        printing.

        The report object is an intermediate format that contains the analysis of the
        survey as a 'raw' data structure. This lets us easily write programs for creating
        different output formats for the same data, as well as creating a separation
        of concerns between analysis and display format that makes both better."""
        html_doc = """<html>
        <head>
        <title> 2016 LessWrong Survey Analysis General Report </title>
        <meta charset="UTF-8">
        <link href="general_report.css" rel="stylesheet">
        </head>
        <body>
        </body>
        </html>"""
        document = BeautifulSoup(html_doc, "html")
        body = document.body
        for group in self._structure.groups():
            group_header = document.new_tag("h2")
            group_header.string = group[0]
            body.append(group_header)
            for key in group[1]:
                if key in self._report:
                    dtype = self._structure[key]['dtype']
                    result = self._report[key]
                    if dtype == "!":
                        formatter = getattr(self, "format_exclamation")
                    else:
                        formatter = getattr(self, "format_{}".format(dtype))
                    result_div = formatter(document, self._structure[key], result)
                    body.append(result_div)
            section_rule = document.new_tag("hr")
            body.append(section_rule)
        return document
                
    def format_Y(self, document, metadata, result):
        container = document.new_tag("div")

        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)
        
        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)

        answers = ["Yes", "No"]
        for answer in answers:
            answer_paragraph = document.new_tag("p")
            answer_paragraph.string = "{}: {} {}".format(answer,
                                                         result[answer + "_count"],
                                                         lsa.percent_from_fraction(
                                                             result[answer + "_fraction"]))
            container.append(answer_paragraph)
        return container
            
            
    def format_N(self, document, metadata, result):
        """Take the result dictionary representing a numeric question and format
        it as HTML."""
        container = document.new_tag("div")
        
        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)

        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)
        
        calculations = ["sum","mean","median","mode","stdev"]
        for calculation in calculations:
            calc_paragraph = document.new_tag("p")
            calc_paragraph.string = "{}: {}".format(calculation.title(),
                                                    result[calculation])
            container.append(calc_paragraph)
        return container

    def format_L(self, document, metadata, result):
        """Take the result dictionary representing a radio list and format it as
        HTML."""
        container = document.new_tag("div")
        
        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)

        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)

        answers = metadata["answers"]
        for answer in answers:
            label = answer["label"]
            answer_paragraph = document.new_tag("p")
            answer_paragraph.string = "{}: {} {}".format(label,
                                                         result[label + "_count"],
                                                         lsa.percent_from_fraction(
                                                             result[label + "_fraction"]))
            container.append(answer_paragraph)
        if metadata["sub_questions"]:
            sub_result = result["sub_questions"][0]
            answer_paragraph = document.new_tag("p")
            answer_paragraph.string = "{}: {} {}".format("Other",
                                                         sub_result["count"],
                                                         lsa.percent_from_fraction(
                                                             sub_result["fraction"]))
            container.append(answer_paragraph)
            
        return container

    def format_M(self, document, metadata, result):
        """Take the result dictionary representing a multiple choice question
        with checkbox/binary answers."""
        container = document.new_tag("div")
        
        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)

        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)

        answer_table = document.new_tag("table")

        answer_table_header = document.new_tag("th")

        header_row = document.new_tag("tr")

        (col_1, col_2, col_3) = (document.new_tag("td"),
                                 document.new_tag("td"),
                                 document.new_tag("td"))
        
        (col_1.string, col_2.string, col_3.string) = ("Question", "Count", "Percent")

        header_row.append(col_1)
        header_row.append(col_2)
        header_row.append(col_3)

        answer_table_header.append(header_row)

        answer_table.append(answer_table_header)
        
        for index in enumerate(metadata["sub_questions"]):
            table_row = document.new_tag("tr")
            
            sub_qdata = metadata["sub_questions"][index[0]]
            sub_result = result["sub_questions"][index[0]]
            label_data = document.new_tag("td")
            yes_count_data = document.new_tag("td")
            yes_percent_data = document.new_tag("td")

            label_data.string = sub_qdata["label"]
            yes_count_data.string = str(sub_result["yes_count"])
            yes_percent_data.string = lsa.percent_from_fraction(sub_result["yes_fraction"])

            table_row.append(label_data)
            table_row.append(yes_count_data)
            table_row.append(yes_percent_data)

            answer_table.append(table_row)

        container.append(answer_table)
        return container

    def format_F(self, document, metadata, result):
        """Represent a multiple choice question with multiple answers."""
        container = document.new_tag("div")
        
        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)

        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)

        answer_table = document.new_tag("table")

        answer_table_header = document.new_tag("th")
        
        columns = sum([list(zipped) for zipped in zip(
            [answer["label"] + " (Count)" for answer in metadata["answers"]],
            [answer["label"] + " (Percent)" for answer in metadata["answers"]])], [])
        
        answer_table_header.append(
            mk_table_row(document, ["Question"] + columns))

        answer_table.append(answer_table_header)
        
        for index in enumerate(metadata["sub_questions"]):
            sub_qdata = metadata["sub_questions"][index[0]]
            sub_result = result["sub_questions"][index[0]]
            row_data = [sub_qdata["label"]]
            for label in [answer["label"] for answer in metadata["answers"]]:
                row_data.append(sub_result[label + "_count"])
                row_data.append(
                    lsa.percent_from_fraction(sub_result[label + "_fraction"])
                    )
            table_row = mk_table_row(document, row_data)
            answer_table.append(table_row)

        container.append(answer_table)
        return container

    def format_exclamation(self, document, metadata, result):
        """Convert a result object representing a dropdown box question to HTML."""
        container = document.new_tag("div")
        
        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)

        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)
        
        for answer in metadata["answers"]:
            answer_paragraph = document.new_tag("p")
            
            a_str = "{}: {} {}".format(answer["label"],
                                       result[answer["label"] + "_count"],
                                       lsa.percent_from_fraction(
                                           result[answer["label"] + "_fraction"])
                                       )
            answer_paragraph.string = a_str
            container.append(answer_paragraph)
        return container

    def format_K(self, document, metadata, result):
        """Convert a result object representing multiple numeric questions
        to HTML."""
        container = document.new_tag("div")
        
        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)

        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)

        answer_table = document.new_tag("table")

        answer_table_header = document.new_tag("th")
        
        answers = ["sum", "mean", "median", "mode", "stdev"]
        table_header_row = mk_table_row(
            document,
            ["Question"] + [answer.title() for answer in answers]
        )
        
        answer_table_header.append(table_header_row)
        answer_table.append(answer_table_header)
        
        for index in enumerate(metadata["sub_questions"]):
            sub_qdata = metadata["sub_questions"][index[0]]
            sub_result = result["sub_questions"][index[0]]
            row_data = [sub_qdata["label"]]
            for answer_label in answers:
                row_data.append(sub_result[answer_label])
            answer_table.append(mk_table_row(document, row_data))

        container.append(answer_table)
        return container
            
    def format_5(self, document, metadata, result):
        """Convert a result object representing a five point rating scale to HTML."""
        container = document.new_tag("div")
        
        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)

        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)

        answers = (1, 2, 3, 4, 5)
        for answer_str in [str(answer) for answer in answers]:
            answer_paragraph = document.new_tag("p")
            a_str = "{}: {} {}".format(answer_str,
                                       result[answer_str + "_count"],
                                       lsa.percent_from_fraction(
                                           result[answer_str + "_fraction"])
                                       )
            answer_paragraph.string = a_str
            container.append(answer_paragraph)
        return container
    
    def format_S(self, document, metadata, result):
        """Prints a message to inform the reader that results for S-type
        questions aren't available."""
        return self.generic_aggregation_error(document, metadata, result)

    def format_Q(self, document, metadata, result):
        """Prints a message to inform the reader that results for S-type
        questions aren't available."""
        return self.generic_aggregation_error(document, metadata, result)

    def format_T(self, document, metadata, result):
        """Prints a message to inform the reader that results for S-type
        questions aren't available."""
        return self.generic_aggregation_error(document, metadata, result)

    def format_X(self, document, metadata, result):
        """Prints a message to inform the reader that results for S-type
        questions aren't available."""
        return self.generic_aggregation_error(document, metadata, result)

    def format_O(self, document, metadata, result):
        """Prints a message to inform the reader that results for S-type
        questions aren't available."""
        return self.generic_aggregation_error(document, metadata, result)

    def generic_aggregation_error(self, document, metadata, result):
        container = document.new_tag("div")
        
        code_header = document.new_tag("h3")
        code_header.string = metadata["code"]
        container.append(code_header)

        question_text = document.new_tag("p")
        question_text.string = metadata["label"]
        container.append(question_text)

        error_small = document.new_tag("small")
        
        error_paragraph = document.new_tag("p")
        error_msg = ("This question was asked in such a way that it can't be " +
                     "aggregated, and therefore can't be included in the general report.")
        error_paragraph.string = error_msg

        error_small.append(error_paragraph)
        
        container.append(error_small)

        return container
    
def mk_table_row(document, data):
    table_row = document.new_tag("tr")
    for item in data:
        table_data = document.new_tag("td")
        table_data.string = str(item)
        table_row.append(table_data)
    return table_row    
    
KF = KeyFormatter(report, structure)
document = KF.format_keys()

print(document.prettify())

#cursor.execute("select count(*) from data;")
#total_respondents = cursor.fetchone()[0]
#cursor.execute("select count(*) from " + view + ";")
#sample_size = cursor.fetchone()[0]
#print("Total survey respondents:", total_respondents)
#print("Respondent surveys used:", sample_size, end="\n\n")


#print(output)
