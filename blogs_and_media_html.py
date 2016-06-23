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
    print("<th>Sample Size</th>\n")
    print("</tr>\n")

def radio_button_header(question):
    """Print a table header for a radio button question."""
    print("<tr>\n")
    print("<th>Cluster</th>")
    for answer in question["answers"]:
        print("<th>{}</th>\n".format(answer["label"]))
    print("<th>Sample Size</th>\n")
    print("</tr>\n")

def multiple_choice_binary_header(question):
    print("<tr>\n")
    print("<th>Cluster</th>\n")
    print("<th>Yes</th>\n")
    print("<th>No</th>\n")
    print("<th>Sample Size</th>\n")
    print("</tr>\n")

def multiple_choice_multiple_answer_header(question):
    print("<tr>\n")
    print("<th>Cluster</th>\n")
    for answer in question["answers"]:
        print("<th>{}</th>\n".format(answer["label"]))
    print("<th>Sample Size</th>\n")
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
        multiple_choice_binary_header(ss[prefix])
        caption = ss[prefix]["sub_questions"][int(index) - 1]["label"]
    elif dtype == "F":
        (prefix, index) = keys[key_idx].split("_")
        multiple_choice_multiple_answer_header(ss[keys[key_idx].split("_")[0]])
        caption = ss[prefix]["sub_questions"][int(index) - 1]["label"]
    print("<caption>{}</caption>".format(caption))
    for cluster_idx in range(9):
        key_values = [row[key_idx] for row in clusters[str(cluster_idx)] 
                      if row[key_idx] and (row[key_idx] != "N/A")]
        cluster_sample_size = len(key_values) if len(key_values) else 1
        if dtype == "N":
            if cluster_sample_size < 10:
                key_values = [] # Trigger N/A for all values if cluster too small
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
            print("<td>{}</td>\n".format(cluster_sample_size))
            print("</tr>\n")
        elif dtype == "L":
            print("<tr>\n")
            print("<td>{}</td>\n".format(cluster_idx))
            if cluster_sample_size < 10:
                for answer in ss[keys[key_idx]]["answers"]:
                    print("<td>N/A</td>\n")
                print("<td>{}</td>\n".format(cluster_sample_size))
                print("</tr>\n")
                continue
            for answer in ss[keys[key_idx]]["answers"]:
                percent = (key_values.count(answer["label"]) 
                           / cluster_sample_size) * 100
                print("<td>", str(round(percent, 3)) + "%" , "</td>")
            print("<td>{}</td>\n".format(cluster_sample_size))
            print("</tr>\n")
        elif dtype == "M":
            key_values = [value for value in key_values if value != "N/A"]
            cluster_sample_size = len(key_values) if len(key_values) else 1
            print("<tr>\n")
            print("<td>{}</td>\n".format(cluster_idx))
            for boolean in ("Yes", "No"):
                count = (key_values.count(boolean) 
                         / cluster_sample_size) * 100
                print("<td>{}</td>\n".format(round(count,3)))
            print("<td>{}</td>\n".format(cluster_sample_size))
            print("</tr>\n")
        elif dtype == "F":
            print("<tr>\n")
            print("<td>{}</td>\n".format(cluster_idx))
            for answer in ss[keys[key_idx].split("_")[0]]["answers"]:
                count = (key_values.count(answer["label"]) 
                         / cluster_sample_size) * 100
                print("<td>{}</td>\n".format(round(count,3)))
            print("<td>{}</td>\n".format(cluster_sample_size))
            print("</tr>\n")
    print("</table>\n")
        

