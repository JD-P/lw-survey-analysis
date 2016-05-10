import time
import re
import statistics
import sqlite3
import json
import libsurveyanalysis as lsa
import matplotlib.pyplot as plt
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("database", help="The database to read the survey results from")
parser.add_argument("--structure", help="The survey structure file.")
parser.add_argument("-j", "--json", 
                    help="Filepath to output JSON representing question " + 
                    "stdevs to.")
arguments = parser.parse_args()

db_conn = sqlite3.connect(arguments.database)
cursor = db_conn.cursor()

change_date = "Fri Mar 25 19:50:41 PDT 2016" # Questions had ranges added on this date
ch_timestamp = time.mktime(time.strptime(change_date, "%a %b %d %H:%M:%S %Z %Y"))

keys = ['rowid',
        'InstructionsConfirm',
        'CalibrationQuestions_1',
        'CalibrationQuestions_2',
        'CalibrationQuestions_3',
        'CalibrationQuestions_4',
        'CalibrationQuestions_5',
        'CalibrationQuestions_6',
        'CalibrationQuestions_7',
        'CalibrationQuestions_8',
        'CalibrationQuestions_9',
        'CalibrationQuestions_10',
        'CalibrationQuestions_11',
        'CalibrationQuestions_12',
        'CalibrationQuestions_13',
        'CalibrationQuestions_14',
        'CalibrationQuestions_15',
        'CalibrationQuestions_16']

cursor.execute("select " + ','.join(keys) + 
               " from data where startdate > ? or submitdate > ?;",
               (ch_timestamp, ch_timestamp))
rows = cursor.fetchall()

column_answers = [[] for i in range(len(keys[2:]))]

column_labels = [
    "Are you smiling right now?",
    "Which is heavier, a virus or a prion?",
    "I'm thinking of a number between one and ten, what is it?",
    'What year was the fast food chain "Dairy Queen" founded? (Within five years)',
    "Alexander Hamilton appears on how many distinct denominations of US Currency?",
    "Without counting, how many keys on a standard IBM keyboard released after 1986, within ten?",
    "What's the diameter of a standard soccerball, in cm within 2?",
    "How many calories in a reese's peanut butter cup within 20?"]

column_outcome_funcs = [
    (lambda p: 1),
    (lambda p: 1 if p == "virus" else 0),
    (lambda p: 1 if p == 4 else 0),
    (lambda p: 1 if p in range(1935,1946) else 0),
    (lambda p: 1 if p == 6 else 0),
    (lambda p: 1 if p in range(91,120) else 0),
    (lambda p: 1 if p in range(20,25) else 0),
    (lambda p: 1 if p in range(85,126) else 0)]

column_outcome_spaces = [2,2,10,316,25,150,50,300]

column_types = [str, str, int, int, int, int, int, int]
for column_indice in range(1,16,2):
    question_indice = int((column_indice - 1) / 2)
    prev_indice = int((column_indice - 1))
    column_answers[prev_indice] = [column_types[question_indice],[]]

def calc_brier(prediction,confidence,
               outcome, outcomes):
    """Calculate the brier score for a single prediction.

    prediction - The value predicted by the forecaster.
    confidence - How much confidence was assigned to the forecast.
    outcome - A function which outputs a binary value based on whether the
    prediction was correct.
    outcomes - The total number of possible outcomes."""
    correctness = outcome(prediction)
    if correctness:
        return (((confidence / 100) - correctness) ** 2)
    else:
        return ((confidence / 100) ** 2) + correctness

for row in rows:
    for column_indice in range(1,16,2):
        prev_indice = int((column_indice - 1))
        answer = row[2:][prev_indice]
        confidence = lsa.val_prob_ans(row[2:][column_indice])
        if confidence:
            column_answers[prev_indice][1].append(answer)
            column_answers[column_indice].append(confidence)
            
for answers_indice in range(1,16,2):
    question_indice = int((answers_indice - 1) / 2)
    prev_indice = int((answers_indice - 1))
    column_type = column_answers[prev_indice][0]
    answers = column_answers[prev_indice][1]
    print(column_labels[question_indice])
    if column_type == str:
        answers = [string.lower().strip().strip(".,a") for string in answers]
        for answer in sorted(list(set(answers))):
            ans_count = answers.count(answer)
            print(answer + ":", ans_count)
    else:
        num_conv = re.compile("[0-9]+")
        num_answers = []
        for answer in answers:
            try:
                match = num_conv.search(answer)
            except TypeError:
                continue
            if match:
                num_answer = float(answer[match.start():match.end()])
                if num_answer > 0 and num_answer < 2017:
                    num_answers.append(num_answer)
        print("Average answer:", statistics.mean(num_answers))
        print("Median answer:", statistics.median(num_answers))
        print("Modal answer:", statistics.mode(num_answers))
    confidences = column_answers[answers_indice]
    print("Average prediction:", statistics.mean(confidences))
    print("Median prediction:", statistics.median(confidences))
    try:
        print("Modal prediction:", statistics.mode(confidences))
    except statistics.StatisticsError:
        print("Modal prediction: Multiple Values Found Equally Likely")
    print(end="\n")

row_scores = []
for row in rows:
    row = row[2:]
    row_prediction_scores = []
    for column_indice in range(1,16,2):
        question_indice = int((column_indice - 1) / 2)
        prev_indice = int((column_indice - 1))
        column_type = column_types[question_indice]
        answer = row[prev_indice]
        confidence = lsa.val_prob_ans(row[column_indice])
        outcome = column_outcome_funcs[question_indice]
        outcomes = column_outcome_spaces[question_indice]
        if not answer:
            continue
        if column_type == str:
            answer = answer.lower().strip().strip(".,a")
            brier = calc_brier(answer,confidence,outcome,outcomes)
            row_prediction_scores.append(brier)
        else:
            num_conv = re.compile("[0-9]+")
            try:
                match = num_conv.search(answer)
            except TypeError:
                continue
            if match:
                num_answer = float(answer[match.start():match.end()])
                brier = calc_brier(num_answer,confidence,outcome,outcomes)
                row_prediction_scores.append(brier)
    N = len(row_prediction_scores)
    if N:
        row_scores.append(sum(row_prediction_scores) * (1 / N))
    else:
        row_scores.append(None)

brier_non_empty = [(value[0],value[1]) 
                   for value in enumerate(row_scores) if value[1]]

def between(num, one, two):
    """Determine if num is between value one and value two. If num is less than 
    the highest number and higher than the lowest number this function returns
    true."""
    if one == two:
        raise ValueError("Number arguments one and two were equal to each other.")
    if one > two and num > two and one > num:
        return True
    elif two > one and num > one and two > num:
        return True
    else:
        return False

def assign_groups(data, stdevs=3, two_tailed=True):
    """Assign brier score rows to n stdev groups.

    data - The data to distribute.
    stdevs - The number of stdevs/groups to distribute across."""
    mean = statistics.mean([value[1] for value in data])
    sigma = statistics.stdev([value[1] for value in data])
    pos_deviations = [sigma * i for i in range(1,stdevs + 1)]
    neg_deviations = list(reversed([-sigma * i for i in range(1,stdevs + 1)]))
    intervals = ([mean + sigma for sigma in neg_deviations] + 
                 [mean] + 
                 [mean + sigma for sigma in pos_deviations])
    intervals_iter = iter(intervals)
    data.sort(key=(lambda t: t[1]))
    indice_pairs = []
    previous = 0
    target = next(intervals_iter)
    for row_score_tuple_indice in enumerate(data[previous:]):
        row_score_tuple = row_score_tuple_indice[1]
        indice = row_score_tuple_indice[0]
        if row_score_tuple[1] > target:
            indice_pairs.append((previous, indice, target))
            previous = indice
            try:
                target = next(intervals_iter)
            except StopIteration:
                break
    return (data,indice_pairs)
        
if arguments.json:
    groups = assign_groups(brier_non_empty)
    outfile = open(arguments.json,"w")
    struct_keys = ['MIRIMission', 'MIRIEffectiveness', 
                   'CFARKnowledge', 'CFARAttendance',
                   'CFAROpinion', 'EAKnowledge', 
                   'EAIdentity', 'EACommunity', 
                   'EADonations', 'EAAnxiety', 
                   'EAOpinion', 'ComplexAffiliation', 
                   'Voting', 'AmericanParties', 
                   'PoliticalInterest', 'AbortionLaws', 
                   'Immigration', 'Taxes', 
                   'MinimumWage', 'Feminism', 
                   'SocialJustice', 'HumanBiodiversity', 
                   'BasicIncome', 'GreatStagnation', 
                   'InstructionsConfirm', 'CalibrationQuestions', 
                   'ProbabilityQuestions','Cryonics', 
                   'CryonicsNow', 'CryonicsPossibility', 
                   'SingularityText', 'SingularityYear', 
                   'SingularityHealth', 'SuperbabiesText', 
                   'ModifyOffspring', 'GeneticTreament', 
                   'GeneticImprovement', 'GeneticCosmetic', 
                   'GeneticOpinionD', 'GeneticOpinionI', 
                   'GeneticOpinionC', 'LudditeFallacy', 
                   'UnemploymentYear', 'EndOfWork', 
                   'EndOfWorkConcerns', 'XRiskType']
    for group_indices_indice in enumerate(groups[1]):
        data = groups[0]
        view_name = "group_" + str(group_indices_indice[0])
        group_indices = group_indices_indice[1]
        if not (abs(group_indices[0] - group_indices[1]) > 2):
            continue
        row_indices = data[group_indices[0]:group_indices[1]]
        # This one deserves some explanation. You grab the row id from the 
        # score tuple, and then you look up the row it corresponds to with it
        # in rows, and then you look up the *database* row id within the row
        # you retrieved.
        group = [rows[score_tuple[0]][0] for score_tuple in row_indices]
        cursor.execute("CREATE TEMP VIEW " + view_name +  
                       " AS SELECT *" + " FROM data WHERE (startdate >  " 
                       + str(ch_timestamp) + " OR submitdate > " + str(ch_timestamp) +  
                       ") AND rowid IN " + "(" +  ','.join(str(id_) for id_ in group) +
                       ")")
        conditions = {
            "Age":"where Age <= 122",
            "IQ":"where 65 < IQ AND IQ < 250",
            "SAT":"where SAT <= 1600 AND SAT > 0",
            "SAT2":"where SAT2 <= 2400 AND SAT2 > 0",
            "ACT":"where ACT <= 36"}
        if not arguments.structure:
            raise ValueError("--json argument requires --structure argument too.")
        else:
            structure = lsa.SurveyStructure(arguments.structure)
        printout = lsa.analyze_keys(struct_keys, db_conn, structure, 
                                    conditions, view_name)
        json.dump((printout,) + groups,outfile)
        print(view_name.upper())
        print("BRIER SCORE INTERVAL:", group_indices[2])
        print("SAMPLE SIZE:", len(group))
        print(printout)
