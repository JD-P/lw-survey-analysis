import sqlite3
from scipy.cluster import vq
import numpy as np
import json 
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("database", help="Filepath to the sqlite database to analyze.")
parser.add_argument("-k", default=18, type=int, 
                    help="The number of centroids to cluster.")
parser.add_argument("-o", "--output", 
                    help="The filepath to write output to, " + 
                    "if not given output written to stdout.") 
arguments = parser.parse_args()

db_conn = sqlite3.connect(arguments.database)
cursor = db_conn.cursor()

keys = ["Age","BirthSex","Gender","Country","Race","SexualOrientation",
        "Asexuality","RelationshipStyle","NumberPartners","RelationshipGoals",
        "Married","LivingWith","Children","MoreChildren","WorkStatus_1",
        "WorkStatus_2","WorkStatus_3","WorkStatus_4","WorkStatus_5","WorkStatus_6",
        "WorkStatus_7","WorkStatus_8","WorkStatus_9","Profession",
        "EducationCredentials","IQ","IQAge","IQType","SAT","SAT2","ACT",
        "PoliticsShort","ReligiousViews","ReligionType","FamilyReligion",
        "ReligiousBackground", "BlogsRead_1","BlogsRead_2","BlogsRead_3",
        "BlogsRead_4","BlogsRead_5", "BlogsRead_6","BlogsRead_7","BlogsRead_8",
        "BlogsRead_9","BlogsRead2_1", "BlogsRead2_2","BlogsRead2_3",
        "BlogsRead2_4","BlogsRead2_5","BlogsRead2_6","BlogsRead2_7","BlogsRead2_8",
        "BlogsRead2_9","StoriesRead_1","StoriesRead_2","StoriesRead_3",
        "StoriesRead_4","StoriesRead_5","StoriesRead_6","StoriesRead_7",
        "StoriesRead_8","StoriesRead_9","StoriesRead2_1","StoriesRead2_2",
        "StoriesRead2_3","StoriesRead2_4","StoriesRead2_5","StoriesRead2_6",
        "StoriesRead2_7","StoriesRead2_8","StoriesRead2_9"]

# Indices of columns whose values are linearly comparable

include_indices = [0,1,2,8,10,12,13,14,15,16,17,18,19,20,21,22,23,24,25,28,29,30]

# Conversion dicts for string answers

blogs_read_answers = {"Regular Reader":1,
                      "Sometimes":(1/6) * 5,
                      "Rarely":(1/6) * 4,
                      "Almost Never":(1/6) * 3,
                      "Never":(1/6) * 2,
                      "Never Heard Of It":(1/6),
                      "http://kajsotala.fi/":0, # Unprincipled Exception
                      None:0}

stories_read_answers = {"Whole Thing":1,
                        "Partially And Intend To Finish":(1/5) * 4,
                        "Partially And Abandoned":(1/5) * 3,
                        "Never":(1/5) * 2,
                        "Never Heard Of It":(1/5),
                        None:0}


cursor.execute("select " + ','.join(keys) + " from data;")

rows = cursor.fetchall()
observations = rows[:]

columns = [field[0] for field in cursor.description]
filtered_columns = [field[1] for field in enumerate(columns) 
                    if field[0] in include_indices]

conversion_dict = {}.fromkeys(columns, None)
for column in filtered_columns:
    cursor.execute("select distinct " + column + " from data;")
    answers = [value[0] for value in cursor.fetchall() if value[0]]
    try:
        answers[0]
    except IndexError:
        continue
    conversion_dict[column] = {}.fromkeys(answers, None)
    if type(answers[0]) == float or type(answers[0]) == int:
        for answer in sorted(answers):
            try:
                conversion_dict[column][answer] = answer / max(answers)
            except TypeError:
                conversion_dict[column][answer] = 0
        conversion_dict[column][None] = 0 - (1/max(answers))
        conversion_dict[column][0] = 0
    elif type(answers[0]) == str:
        step = 1 / len(answers)
        answer_value = step
        for answer in sorted(answers):
            conversion_dict[column][answer] = answer_value
            answer_value += step
        conversion_dict[column][None] = 0
    else:
        print(answers)
        raise ValueError("Non numeric or string value found in database.")

# Create a translation dictionary to output with the clusters so that values can be
# converted back to string values
#translation_dict = {}
#for column in conversion_dict.keys():
#    indice = keys.index(column)
#    translation_dict[indice] = {}
#    for answer in conversion_dict[column]:
#        value = conversion_dict[column][answer]
#        translation_dict[indice][value] = answer

# Normalize values so they're all in the same range

for observation in enumerate(observations):
    observations[observation[0]] = list(observation[1])

for observation in observations:
    for answer in enumerate(observation):
        if answer[0] in include_indices:
            try:
                observation[answer[0]] = float(
                    conversion_dict[columns[answer[0]]][answer[1]]
                )
            except:
                print(conversion_dict, answer, columns[answer[0]])
        else:
            if answer[0] in range(36,54):
                try:
                    observation[answer[0]] = float(
                        blogs_read_answers[observation[answer[0]]]
                    )
                except KeyError:
                    pass
            elif answer[0] in range(54, 71):
                observation[answer[0]] = float(
                    stories_read_answers[observation[answer[0]]]
                )
            else:
                observation[answer[0]] = 0
            
observations = np.array(observations)

K = arguments.k
clusters = {}
for i in range(K):
    clusters[i] = []
kmeans_indexes = vq.vq(observations, vq.kmeans(observations, K)[0])[0]
for index in enumerate(kmeans_indexes):
    clusters[index[1]].append(rows[index[0]])

# Output the names of the columns and the clusters found by k-means.
output = [keys, clusters]
if arguments.output:
    outfile = open(arguments.output, "w")
    json.dump(output, outfile)
else:
    print(output)
