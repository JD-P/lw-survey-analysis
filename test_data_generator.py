from random import randrange
import sqlite3
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("sqlite_output", help="The filepath to write sqlite db to.")
parser.add_argument("json_output", help="The filepath to write json debug info to.")
arguments = parser.parse_args()

def generate(database_path, json_path):
    """Generate test data for the libsurveyanalysis.

    There are eight columns in the table outputted by the generator, each 
    corresponding to a limesurvey question type, plus however many are provided
    by sub questions which must have their own column. These provide representative
    test data, then a second JSON file is output that includes debug information
    such as the true count of the data in various measures such as mean and stdev.

    This allows the libsurveyanalysis test suite to know that it has the correct 
    counts from the libsurveyanalysis. (Don't think too hard about how this test 
    data generator knows what the right count is.)"""
    row_components = []
    nd = generate_numeric_data()
    row_components.append(nd[0])
    bd = generate_binary_data()
    row_components.append(bd[0])
    ld = generate_list_data()
    row_components.append(ld[0])
    mbcd = generate_multiple_binary_choice_data()
    row_components.append(mbcd[0][0])
    row_components.append(mbcd[0][1])
    mamcd = generate_multiple_answer_multiple_choice_data()
    row_components.append(mamcd[0][0])
    row_components.append(mamcd[0][1])
    row_components.append(mamcd[0][2])
    dd = generate_dropdown_data()
    row_components.append(dd[0])
    mnd = generate_multiple_numeric_data()
    row_components.append(mnd[0][0])
    row_components.append(mnd[0][1])
    fpd = generate_five_point_rating_data()
    row_components.append(fpd[0])
    
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS test_data (Age INT, Binary TEXT, List TEXT," +
                   " mbc_1 TEXT, mbc_2 TEXT, mamc_1 TEXT, mamc_2 TEXT, mamc_3 TEXT," +
                   " dd TEXT, mn_1 INT, mn_2 INT, fp INT);") 
    for row in zip(*row_components):
        cursor.execute("INSERT INTO test_data VALUES (" +
                       ",".join(["'{}'"] * 12).format(*row) + ");")
    connection.commit()
        
def generate_numeric_data():
    """Generate random test data in the range of human ages for the 
    numeric question analyzer."""
    debug_info = {}
    debug_info["test_answers"] = {}
    test_data = []
    for i in range(500):
        row_item = randrange(13,123)
        test_data.append(row_item)
        if row_item in debug_info["test_answers"]:
            debug_info["test_answers"][row_item] += 1
        else:
            debug_info["test_answers"][row_item] = 1
    return (test_data, debug_info)

def generate_binary_data():
    """Generate random test data for the binary question analyzer."""
    yes = 500
    no = randrange(50, 300)
    yes -= no
    test_data = (["Yes"] * yes) + (["No"] * no)
    debug_info = {"test_answers":{"Yes":yes, "No":no}}
    return (test_data, debug_info)

def generate_list_data():
    """Generate test data for the radio button/list question analyzer."""
    #Assume the question is "What's your favorite color?"
    red = 100
    blue = 200
    green = 125
    yellow = 75

    test_data = ((["red"] * red) +
                 (["blue"] * blue) +
                 (["green"] * green) +
                 (["yellow"] * yellow))
    debug_info = {"test_answers":{"red":red, "blue":blue,
                                  "green":green, "yellow":yellow}}
    return (test_data, debug_info)

def generate_multiple_binary_choice_data():
    """Generate test data for the multiple binary choice question analyzer."""
    debug_info = {}
    debug_info["test_answers"] = {}
    question_data = {}
    question_data["sub_questions"] = []
    question_data["code"] = "mbc"

    subquestion_1 = {}
    subquestion_1["code"] = "1"
    
    subquestion_2 = {}
    subquestion_2["code"] = "2"

    question_data["sub_questions"].append(subquestion_1)
    question_data["sub_questions"].append(subquestion_2)
    debug_info["question_data"] = question_data

    sub1_yes = 300
    sub1_no = 200

    sub2_yes = 200
    sub2_no = 300

    debug_info["test_answers"] = {"mbc_1":{"Yes":sub1_yes,
                                           "No":sub1_no},
                                  "mbc_2":{"Yes":sub2_yes,
                                           "No":sub2_no}}
    
    sub1_data = sum([["Yes"] * sub1_yes,
                     ["No"] * sub1_no], [])
    sub2_data = sum([["Yes"] * sub2_yes,
                     ["No"] * sub2_no], [])

    test_data = (sub1_data, sub2_data)

    return (test_data, debug_info)

def generate_multiple_answer_multiple_choice_data():
    """Generate test data for the multiple answer multiple choice question analyzer."""
    debug_info = {}

    # Assume the question is "do you like this kind of pie?"
    # Yes it's silly but.
    question_data = {}
    question_data["answers"] = ({"label":"Yes"},
                                {"label":"Sorta"},
                                {"label":"No"})
    question_data["code"] = "mamc"
    debug_info["question_data"] = question_data
    
    subquestion_1 = {}
    subquestion_1["code"] = "1"

    subquestion_2 = {}
    subquestion_2["code"] = "2"

    subquestion_3 = {}
    subquestion_3["code"] = "3"

    question_data["sub_questions"] = []
    question_data["sub_questions"].append(subquestion_1)
    question_data["sub_questions"].append(subquestion_2)
    question_data["sub_questions"].append(subquestion_3)
    
    sub1_numbers = {"Yes":250,
                    "Sorta":150,
                    "No":100}
    sub1_data = sum([["Yes"] * sub1_numbers["Yes"],
                    ["Sorta"] * sub1_numbers["Sorta"],
                    ["No"] * sub1_numbers["No"]], [])

    sub2_numbers = {"Yes":100,
                    "Sorta":250,
                    "No":150}
    sub2_data = sum([["Yes"] * sub2_numbers["Yes"],
                    ["Sorta"] * sub2_numbers["Sorta"],
                    ["No"] * sub2_numbers["No"]], [])

    sub3_numbers = {"Yes":150,
                    "Sorta":100,
                    "No":250}
    sub3_data = sum([["Yes"] * sub3_numbers["Yes"],
                    ["Sorta"] * sub3_numbers["Sorta"],
                    ["No"] * sub3_numbers["No"]], [])
    
    test_data = (sub1_data, sub2_data, sub3_data)
    debug_info["test_answers"] = {"mamc_1":sub1_numbers,
                                  "mamc_2":sub2_numbers,
                                  "mamc_3":sub3_numbers}
    return (test_data, debug_info)

def generate_dropdown_data():
    """Generate test data for the dropdown question analyzer."""
    red = 100
    blue = 200
    green = 125
    yellow = 75

    test_data = ((["red"] * red) +
                 (["blue"] * blue) +
                 (["green"] * green) +
                 (["yellow"] * yellow))
    debug_info = {"test_answers":{"red":red, "blue":blue,
                                  "green":green, "yellow":yellow}}
    return (test_data, debug_info)

def generate_multiple_numeric_data():
    """Generate test data for the multiple numeric question analyzer."""
    # Assume the two subquestions are ACT score out of 36 and SAT out of 2400
    debug_info = {}

    question_data = {}
    question_data["code"] = "mn"

    subquestion_1 = {}
    subquestion_1["code"] = 1

    subquestion_2 = {}
    subquestion_2["code"] = 2

    question_data["sub_questions"] = []
    question_data["sub_questions"].append(subquestion_1)
    question_data["sub_questions"].append(subquestion_2)
    
    debug_info["test_answers"] = {}
    
    sub1_data = []
    debug_info["test_answers"]["mn_1"] = {}
    for i in range(500):
        sub_item_1 = randrange(0, 37)
        sub1_data.append(sub_item_1)
        if sub_item_1 in debug_info["test_answers"]["mn_1"]:
            debug_info["test_answers"]["mn_1"][sub_item_1] += 1
        else:
            debug_info["test_answers"]["mn_1"][sub_item_1] = 1
    sub2_data = []
    debug_info["test_answers"]["mn_2"] = {}
    for i in range(500):
        sub_item_2 = randrange(0,2401)
        sub2_data.append(sub_item_2)
        if sub_item_2 in debug_info["test_answers"]["mn_2"]:
            debug_info["test_answers"]["mn_2"][sub_item_2] += 1
        else:
            debug_info["test_answers"]["mn_2"][sub_item_2] = 1
    test_data = (sub1_data, sub2_data)
    return (test_data, debug_info)

def generate_five_point_rating_data():
    """Generate test data for the five point rating question analyzer."""
    debug_info = {}
    debug_info["question_data"] = {"code":"fp"}
    debug_info["test_answers"] = {1:100,
                                  2:100,
                                  3:100,
                                  4:100,
                                  5:100}
    test_data = sum([[1] * 100,
                     [2] * 100,
                     [3] * 100,
                     [4] * 100,
                     [5] * 100],[])
    return (test_data, debug_info)

generate(arguments.sqlite_output, arguments.json_output)
