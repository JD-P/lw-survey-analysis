import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("database", help="The sqlite3 file to read survey data from.")
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

for i in range(1,23):
    try:
        community_name = community_names[i - 1]
    except IndexError:
        print(len(community_names), i)
    print(community_name, "stats:")
    cursor.execute('select count(*) from data where ActiveMemberships_' +
                   str(i) + ' is "Yes";')
    community_members = cursor.fetchone()[0]
    print("Sample Size:", community_members)
    for condition in keys:
        cursor.execute('select count(*) from data where ' 
                       + condition + ' != "No" AND ' + "ActiveMemberships_" 
                       + str(i) + ' is "Yes";')
        condition_count = cursor.fetchone()[0]
        print(condition + ":", condition_count / community_members)
    print("\n")
