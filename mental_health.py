import sqlite3
import os.path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rc('xtick', labelsize='7')
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("database", help="The sqlite3 file to read survey data from.")
parser.add_argument("-t", "--text", action="store_true", 
                    help="Do text output instead of charts.")
parser.add_argument("-d", "--directory", help="Directory to write charts to.")
arguments = parser.parse_args()

db_conn = sqlite3.connect(arguments.database)
cursor = db_conn.cursor()

# Number of survey respondents with at least one mental health problem
keys = ["Depression", "OCD", "ASD", 
        "ADHD", "BipolarDisorder", "AnxietyDisorder", 
        "BPD", "Schizophrenia", "SubstanceUseDisorder", 
        "SubstanceUseWonder", "SubstanceUseWorry"]
cursor.execute("select count(*) from data;")
total = cursor.fetchone()[0]
cursor.execute("select count(*) from data where " 
               + ' is not "No" OR '.join(keys) + ' is not "No";')
neurotypicals = cursor.fetchone()[0]
print("Number of survey respondents:", total)
print("Number of survey respondents who reported at least one mental health",
      "problem:", neurotypicals)

community_names = ["LessWrong", "LessWrong Meetups", "LessWrong Facebook Group",
                   "LessWrong Slack", "SlateStarCodex", "Rationalist Tumblr", 
                   "Rationalist Facebook", "Rationalist Twitter", 
                   "Effective Altruism Hub", "FortForecast", 
                   "Good Judgement(TM) Open", "PredictionBook", "Omnilibrium", 
                   "Hacker News", "#lesswrong on freenode", 
                   "#slatestarcodex on freenode", "#hplusroadmap on freenode", 
                   "#chapelperilous on freenode", "/r/rational", "/r/HPMOR", 
                   "/r/SlateStarCodex", 
                   "One or more private 'rationalist' groups"]

conditions_by_community = {}
for i in range(1,23):
    try:
        community_name = community_names[i - 1]
    except IndexError:
        print(len(community_names), i)
    cursor.execute('select count(*) from data where ActiveMemberships_' +
                   str(i) + ' is "Yes";')
    community_members = cursor.fetchone()[0]
    conditions_by_community[community_name] = [{},community_members]
    for condition in keys:
        cursor.execute('select count(*) from data where ' 
                       + condition + ' != "No" AND ' + "ActiveMemberships_" 
                       + str(i) + ' is "Yes";')
        condition_count = cursor.fetchone()[0]
        conditions_by_community[community_name][0][condition] = condition_count
        
    
if arguments.text:
    for i in range(1,23):
        community_name = community_names[i - 1]
        print(community_name, "stats:")
        community_members = conditions_by_community[community_name][1]
        print("Sample Size:", community_members)
        conditions = sorted(conditions_by_community[community_name][0].keys())
        for condition in conditions:
            condition_count = conditions_by_community[community_name][0][condition]
            print(condition + ":", condition_count / community_members)
        print("\n")
else:
    conditions = sorted(conditions_by_community["LessWrong"][0].keys())
    for condition in conditions:
        community_labels = sorted(conditions_by_community.keys())
        community_values = []
        for community in community_labels:
            c_members = conditions_by_community[community][1]
            community_values.append(
                conditions_by_community[community][0][condition] / c_members)
        N = len(community_labels)
        assert len(community_labels) == 22
        colors = ['green', 'lime', 'cyan', '#8f9528', '#c1b34c', 'blue',
                  '#3fffdd', 'magenta', 'black', '#8f3fff', '#117aff', '#ffdd11',
                  'yellow', 'red', '#ff9511', '#004933', '#596561', '#ff8992',
                  '#5900f1', '#b10000', '#00abff', '#003651', '#2d2b0f']
        c_colors = {'Rationalist Tumblr': '#3fffdd', 'FortForecast': '#117aff', 
                    'LessWrong Facebook Group': '#8f9528', 'LessWrong': 'green', 
                    'Rationalist Twitter': 'black', 'SlateStarCodex': 'blue', 
                    'Hacker News': '#ff9511', '#lesswrong on freenode': '#004933', 
                    '#slatestarcodex on freenode': '#596561', '#hplusroadmap on freenode': '#ff8992', 
                    'Rationalist Facebook': 'magenta', 'Omnilibrium': 'red', 
                    'Effective Altruism Hub': '#8f3fff', 
                    "One or more private 'rationalist' groups": '#2d2b0f', 
                    '/r/SlateStarCodex': '#003651', 'PredictionBook': 'yellow', 
                    'LessWrong Meetups': 'lime', 'Good Judgement(TM) Open': '#ffdd11', 
                    '/r/HPMOR': '#00abff', '#chapelperilous on freenode': '#5900f1', 
                    'LessWrong Slack': '#c1b34c', '/r/rational': '#b10000'}
        labels = []
        for community in community_labels:
            labels.append(community + " (Size: " + 
                          str(conditions_by_community[community][1]) + ")")
        ind = np.arange(N)
        width = 0.15
        
        fig, ax = plt.subplots()
        rects = ax.bar(ind * 0.5, community_values, width, color='b')
        for community in enumerate(community_labels):
            rects[community[0]].set_color(c_colors[community[1]])
        ax.set_ylabel('Percentage of people with condition'.title())
        ax.set_title(condition.title())
        ax.set_xticks([])
        #ax.set_xticklabels(community_labels, stretch="condensed")
        # Shrink current axis by 20%
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height * 1.5])
        ax.legend(rects, labels, loc='left center', bbox_to_anchor=(1, 1))
        if arguments.directory:
            plt.savefig(os.path.join(arguments.directory, condition + '.png'),
                        bbox_inches='tight')
        else:
            plt.show()
