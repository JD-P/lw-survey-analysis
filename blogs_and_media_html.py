import json
import statistics
import numpy as np
import libsurveyanalysis
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("clusters", 
                    help="The json file containing the cluster information.")
parser.add_argument("structure",
                    help="The file containing the survey structure.")
parser.add_argument("-t", "--text", action="store_true",
                    help="Output a text report of the analysis.")
arguments = parser.parse_args()

with open(arguments.clusters) as infile:
    (keys, clusters) = json.load(infile)

ss = libsurveyanalysis.SurveyStructure(arguments.structure)

# Print a table of each questions answers across all nine clusters
# Each row represents a cluster, the columns are different 'answers' to the question
# In the case of numeric questions it's different metrics of answer

def numeric_header():
    """Print the table header for a numeric question type."""
    print("<tr>\n")
    print("<th>Cluster</th>\n")
    print("<th>Sum</th>\n")
    print("<th>Mean</th>\n")
    print("<th>Median</th>\n")
    print("<th>Mode</th>\n")
    print("<th>Stdev</th>\n")
    print("</tr>\n")

def radio_button_header(question):
    """Print a table header for a radio button question."""
    print("<tr>\n")
    for answer in question["answers"]:
        print("<td>{}</td>\n".format(answer["label"]))
    print("</tr>\n")

def multiple_choice_binary_header(question, index):
    print("<tr>\n")
    print("<th>Cluster</th>\n")
    for sub_question in question["sub_questions"]:
        print("<th>{}</th>".format(sub_question["label"]))
    print("</tr>\n")

for key_idx in range(len(keys)):
    print("<table>\n")
    key = keys[key_idx]
    try:
        dtype = ss[keys[key_idx].replace("_", "")]["dtype"]
    except KeyError:
        dtype = ss[keys[key_idx].split("_")[0]]["dtype"]
    if dtype == "N":
        numeric_header()
        caption = ss[keys[key_idx].replace("_", "")]["label"]
    elif dtype == "L":
        radio_button_header(ss[keys[key_idx].replace("_", "")])
        caption = ss[keys[key_idx].replace("_", "")]["label"]
    elif dtype == "M":
        (prefix, index) = keys[key_idx].split("_")
        multiple_choice_binary_header(ss[prefix], index)
        caption = ss[prefix]["label"]
    print("<caption>{}</caption>".format(caption))
    for cluster_idx in range(9):
        key_values = [row[key_idx] for row in clusters[str(cluster_idx)] if row[key_idx]]
        cluster_sample_size = len(key_values) if len(key_values) else 1
        if dtype == "N":
            print("<tr>\n")
            print("<td>", cluster_idx, "</td>\n")
            print("<td>", round(sum(key_values), 3), "</td>\n")
            try:
                print("<td>", round(statistics.mean(key_values), 3), "</td>\n")
            except statistics.StatisticsError:
                print("<td>", "N/A", "</td>\n")
            try:
                print("<td>", round(statistics.median(key_values), 3), "</td>\n")
            except statistics.StatisticsError:
                print("<td>", "N/A", "</td>\n")
            try:
                print("<td>", round(statistics.mode(key_values), 3), "</td>\n")
            except statistics.StatisticsError:
                print("<td>", "N/A", "</td>\n")
            try:
                print("<td>", round(statistics.stdev(key_values), 3), "</td>\n")
            except statistics.StatisticsError:
                print("<td>", "N/A", "</td>\n")
            print("</tr>\n")
        elif dtype == "L":
            print("<tr>\n")
            for answer in ss[keys[key_idx]]["answers"]:
                percent = (key_values.count(answer["label"]) 
                           / cluster_sample_size) * 100
                print("<td>", str(round(percent, 3)) + "%" , "</td>")
            print("</tr>\n")
        elif dtype == "M":
            print("<tr>\n")
            for sub_question in ss[keys[key_idx]]["sub_questions"]:
                count = (key_values.count(sub_question["label"]) 
                         / cluster_sample_size) * 100
                print("<td>{}</td>\n".format(count))
            print("</tr>\n")
    print("</table>\n")
        

