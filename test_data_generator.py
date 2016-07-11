from random import randrange
import sqlite3
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--sqlite-output", help="The filepath to write sqlite db to.")
parser.add_argument("--json-output", help="The filepath to write json debug info to.")
arguments = parser.parse_args()

def generate():
    """Generate test data for the libsurveyanalysis.

    There are eight columns in the table outputted by the generator, each 
    corresponding to a limesurvey question type, plus however many are provided
    by sub questions which must have their own column. These provide representative
    test data, then a second JSON file is output that includes debug information
    such as the true count of the data in various measures such as mean and stdev.

    This allows the libsurveyanalysis test suite to know that it has the correct 
    counts from the libsurveyanalysis. (Don't think too hard about how this test 
    data generator knows what the right count is.)"""


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
    sub1_no = 300

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

