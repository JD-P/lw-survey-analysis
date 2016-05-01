import json
import statistics
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rc('xtick', labelsize='7')
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("clusters", 
                    help="The json file containing the cluster information.")
parser.add_argument("-t", "--text", action="store_true",
                    help="Output a text report of the analysis.")
arguments = parser.parse_args()

with open(arguments.clusters) as infile:
    (keys, clusters) = json.load(infile)

blog_names = ["LessWrong", "SlateStarCodex", "Overcoming Bias",
              "Minding Our Way", "Agenty Duck", 
              "Eliezer Yudkowsky's Facebook Page", "Luke Muehlhauser",
              "Gwern.net", "Siderea", "Ribbon Farm", 
              "Bayesed And Confused", "The Unit Of Caring", "Givewell Blog",
              "Thing Of Things", "The Last Psychiatrist", "Hotel Concierge",
              "The View From Hell", "Xenosystems"]

blog_names_dict = {}.fromkeys(range(36,54))
for indice in sorted(blog_names_dict.keys()):
    try:
        blog_names_dict[indice] = blog_names[indice - 36]
    except:
        print(indice)
story_names = ["Harry Potter And The Methods Of Rationality",
               "Significant Digits",
               "Three Worlds Collide",
               "The Fable of the Dragon-Tyrant",
               "The World of Null-A",
               "Synthesis",
               "Worm",
               "Pact",
               "Twig",
               "Ra",
               "My Little Pony: Friendship Is Optimal",
               "Friendship Is Optimal: Caelum Est Conterrens",
               "Ender's Game",
               "The Diamond Age",
               "Consider Phlebas",
               "The Metamorphosis Of Prime Intellect",
               "Accelerando",
               "A Fire Upon The Deep"]

story_names_dict = {}.fromkeys(range(54,71))
for indice in sorted(story_names_dict.keys()):
    story_names_dict[indice] = story_names[indice - 54]

cluster_answer_sets = []
for cluster_indice in sorted(clusters.keys()):
    cluster = clusters[cluster_indice]
    cluster_answers = {}
    for row in cluster:
        for key in enumerate(keys):
            if key[1] in cluster_answers:
                cluster_answers[key[1]].append(row[key[0]])
            else:
                cluster_answers[key[1]] = [row[key[0]]]
    cluster_answer_sets.append(cluster_answers)

if arguments.text:
    for cluster_ans_indice in enumerate(cluster_answer_sets):
        cluster_indice = cluster_ans_indice[0]
        cluster_answers = cluster_ans_indice[1]
        print("\nCluster " + str(cluster_indice) + ":", end="\n\t")
        for key_enumerated in enumerate(keys):
            key = key_enumerated[1]
            indice = key_enumerated[0]
            if indice in blog_names_dict:
                label = blog_names_dict[indice]
            elif indice in story_names_dict:
                label = story_names_dict[indice]
            else:
                label = key
            for answer in set(cluster_answers[key]):
                if answer:
                    column_type = type(answer)
                    break
            if column_type == int or column_type == float:
                values = [value for value in cluster_answers[key] if value]
                if values:
                    print("Average", label + ":", statistics.mean(values))
                else:
                    print("Average", label + ": No Answers Provided")
            else:
                print(label, "Answers:", end="\n\t\t")
                for answer in set(cluster_answers[key]):
                    if answer == None:
                        answer = "None"
                    answer_count = cluster_answers[key].count(answer)
                    print(answer + ":", answer_count / len(cluster_answers[key]),
                          end="\n\t\t")
            print(end="\n\t")

    def label_key(key, indice, dicts):
        """Label a given key if it appears in the blog or story names 
        dictionaries.

        Key - The actual string key from keys.
        Indice - The index position of the key in keys.
        Dicts - A tuple containing the blog_names_dict and story_names_dict."""
        blog_names_dict = dicts[0]
        story_names_dict = dicts[1]
        if indice in blog_names_dict:
            label = blog_names_dict[indice]
        elif indice in story_names_dict:
            label = story_names_dict[indice]
        else:
            label = key
        return label

    def collect_answers(key, cluster_answer_sets):
        """Aggregate the results of the answer set from each cluster for a given
        key to study.
        
        Key - String key representing the database column to study.
        cluster_answer_sets - List of dictionaries containing the answers for 
            a given cluster for each column in the row by key."""
        cluster_results = [None, [], set()]
        for cluster_ans_indice in enumerate(cluster_answer_sets):
            cluster_indice = cluster_ans_indice[0]
            cluster_answers = cluster_ans_indice[1]
            for answer in set(cluster_answers[key]):
                if answer:
                    column_type = type(answer)
                    break
            try:
                column_type
            except UnboundLocalError:
                column_type = None
            if column_type == int or column_type == float:
                cluster_results[0] = float
                values = [value for value in cluster_answers[key] if value]
                if values:
                    cluster_results[1].append(statistics.mean(values))
                else:
                    cluster_results[1].append(None)
            else:
                cluster_results[0] = str
                aggregated_answers = []
                for answer in sorted([value for value in set(cluster_answers[key]) 
                                      if value]):
                    cluster_results[2].add(answer)
                    aggregated_answers.append(cluster_answers[key].count(answer)
                                              / len(cluster_answers[key]))
                if None in set(cluster_answers[key]):
                    cluster_results[2].add(None)
                    aggregated_answers.append(cluster_answers[key].count(None)
                                              / len(cluster_answers[key]))
                cluster_results[1].append(aggregated_answers)
        if None in cluster_results[2]:
            cluster_results[2] = sorted([value for value in cluster_results[2]
                                         if value])
            cluster_results[2].append("None")
        else:
            cluster_results[2] = sorted([value for value in cluster_results[2]])
        return cluster_results

    for key_enumerated in enumerate(keys):
        key = key_enumerated[1]
        indice = key_enumerated[0]
        label = label_key(key, indice, 
                          (blog_names_dict, story_names_dict))
        cluster_results = collect_answers(key, cluster_answer_sets)
        if not cluster_results[2]:
            cluster_results[2].append('')
        # Determine height of the output print
        if cluster_results[0] == str:
            result_lengths = []
            for results in cluster_results[1]:
                result_lengths.append(len(results))
            height = max(result_lengths)
        else:
            height = 1
        columns = []
        for i in range(height):
            columns.append([])
        for results in cluster_results[1]:
            if cluster_results[0] == str:
                for result in enumerate(results):
                    columns[result[0]].append(str(result[1]))
            else:
                columns[0].append(str(results))
        print(label)
        for answer_label in cluster_results[2]:
            print(answer_label, end="\t")
        print(end="\n")
        for cluster in range(len(cluster_answer_sets)):
            print("Cluster", str(cluster + 1) + ":", end=" ")

            for column in enumerate(columns):
                try:
                    print(column[1][cluster], end=" | ")
                except IndexError:
                    print("N/A", end=" | ")
            print(end="\n")
        print(end="\n")
#else:
#    for key_enumerated in enumerate(keys):
#        for cluster_ans_indice in enumerate(cluster_answer_sets):
#            cluster_indice = cluster_ans_indice[0]
#            cluster_answers = cluster_ans_indice[1]
