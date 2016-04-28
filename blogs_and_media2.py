import json
import statistics
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("clusters", 
                    help="The json file containing the cluster information.")
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
    print("\nCluster " + cluster_indice + ":", end="\n\t")
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
