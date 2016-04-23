import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("database", help="The filepath to the sqlite3 db.")
arguments = parser.parse_args()

db_conn = sqlite3.connect(arguments.database)
cursor = db_conn.cursor()

keys = ["ComplexAffiliation", "Voting", "AmericanParties", "PoliticalInterest", 
        "AbortionLaws_SQ001", "Immigration_SQ001", "Taxes_SQ001", 
        "MinimumWage_SQ001", "Feminism_SQ001", "SocialJustice_SQ001", 
        "HumanBiodiversity_SQ001", "BasicIncome_SQ001", "GreatStagnation_SQ001", 
        "ModifyOffspring", "GeneticTreament", "GeneticImprovement",
        "GeneticCosmetic","GeneticOpinionD","GeneticOpinionI","GeneticOpinionC",
        "LudditeFallacy","UnemploymentYear","EndOfWork"]

cursor.execute("select " + ','.join(keys) + " from data;")
rows = cursor.fetchall()

#for row_enum in enumerate(rows):
#    rows[row_enum[0]] = list(row_enum[1])
#    row = rows[row_enum[0]]
#    row[4] = {"Pro-Life":0, "Lean Pro-Life":1, "No strong opinion":2, 
#              "Lean Pro-Choice":3, "Pro-Choice":4}[row[4]]

#    row[5] = {"Should be more open":0, "Lean more open":1, "No strong opinion":2, 
#              "Lean more restricted":3, "Should be more restricted":4}[row[5]]

#    row[6] = {"Should be lower":0, "Lean towards lower":1, "No strong opinion":2, 
#              "Lean towards higher":3, "Should be higher":4}[row[6]]

#    row[7] = {"Should be lower or eliminated":0, "Lean towards lower or eliminated":1, 
#              "No strong opinion":2, "Lean towards higher":3, "Should be higher":4}[row[7]]

#    row[8] = {"Very unfavorable":0, "Unfavorable":1, "No strong opinion":2, 
#              "Favorable":3, "Very Favorable":4}[row[8]]

#    row[9] = {"Very unfavorable":0, "Unfavorable":1, "No strong opinion":2, 
#              "Favorable":3, "Very Favorable":4}[row[9]]

#    row[10] = {"Very unfavorable":0, "Unfavorable":1, "No strong opinion":2, 
#               "Favorable":3, "Very Favorable":4}[row[10]]

#    row[11] = {"Strongly oppose":0, "Oppose":1, "No strong opinion":2, "Support":3, 
#               "Strongly support":4}[row[11]]

#    row[12] = {"Strongly doubt":0, "Doubt":1, "No strong opinion":2, "Believe":3, 
#               "Strongly believe":4}[row[12]]

# Obvious analysis, political opinions by affiliation

cursor.execute("select ComplexAffiliation from data;")
# Concatenate the single valued rows, grab their unique values with set() and then
# convert back into a list so we can guaruntee an output order.
affiliations = []
for row in cursor.fetchall():
    if row[0]:
        affiliations += row
affiliations = list(set(affiliations))
affiliations.sort()

for affiliation in affiliations:
    cursor.execute("select " + ','.join(keys) + " from data where " + 
                   "ComplexAffiliation=?;", [affiliation])
    affil_rows = cursor.fetchall()
    keysets = {}.fromkeys(keys)
    print("\n" + affiliation, "Statistics:")
    print("Sample Size:", len(affil_rows), end="\n\t")
    for key in keysets:
        keysets[key] = set()
    # Get the response sets for each question
    for row in affil_rows:
        for key in enumerate(keys):
            if row[key[0]]:
                keysets[key[1]].add(row[key[0]])
    # Count the responses for each question and print results
    for key in sorted(keysets.keys()):
        print(key + ":", end="\n\t\t")
        cursor.execute("select count (" + key 
                       + ") from data where ComplexAffiliation=?;",[affiliation])
        question_total = cursor.fetchone()[0]
        for response in keysets[key]:
            cursor.execute("select count(" + key + ") from data where " + 
                           key + "=? AND ComplexAffiliation=?;", 
                           [response, affiliation])
            response_total = cursor.fetchone()[0]
            try:
                print(response + ":", response_total / question_total, 
                      end="\n\t\t")
            except TypeError:
                continue
        print("\n", end='\t')
