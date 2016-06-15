import statistics
import libsurveyanalysis as lsa
import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("database", help="The database filepath to read survey results from.")
arguments = parser.parse_args()

db_conn = sqlite3.connect(arguments.database)
cursor = db_conn.cursor()

# Determine how many people skipped the Basilisk questions

cursor.execute("SELECT count(*) FROM data WHERE RokoKnowledge IS NULL AND Depression NOT NULL;")
null_skips = cursor.fetchone()[0]
print("People who refused to answer whether they'd heard of Roko's Basilisk but",
      "went on to answer the Depression question:", null_skips)

cursor.execute("SELECT count(*) FROM data WHERE RokoKnowledge = 'No';")
no_skips = cursor.fetchone()[0]
print("People who said they didn't know what the Basilisk is:", no_skips)

# How many people said they didn't know what the Basilisk was but thought it was 
# correct.

cursor.execute("SELECT count(*) FROM data WHERE RokoKnowledge = \"No but I've heard of it\"" + 
               " AND BasiliskCorrectness = 'Yes';")
ignorant_yes = cursor.fetchone()[0]
print("People who said the Basilisk is correct but don't know what it is:", 
      ignorant_yes)

# Correlation between Basilisk worry and autism/OCD/anxietydisorder/schizophrenia

print("<table>\n")
print("<caption>Mental Health Conditions Versus Basilisk Worry</caption>")
print("<tr>\n",
      "<th>Condition</th>\n",
      "<th>Worried</th>\n",
      "<th>Worried But They Worry About Everything</th>\n",
      "<th>Combined Worry</th>\n",
      "</tr>\n")

cursor.execute("SELECT count(*) FROM data WHERE BasiliskAnxiety NOT NULL;")
sample_size = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE BasiliskAnxiety = 'Yes';")
base_yes = cursor.fetchone()[0]
cursor.execute("SELECT count(*) FROM data WHERE BasiliskAnxiety = 'Yes but only because I worry about everything';")
base_yes_but = cursor.fetchone()[0]

print("  <tr>\n")
print("    <td>Baseline</td>\n",
      "    <td>{}%</td>\n".format(str(round(base_yes / sample_size,3) * 100)),
      "    <td>{}%</td>\n".format(str(round(base_yes_but / sample_size,3) * 100)),
      "    <td>{}%</td>\n".format(str(round((base_yes + base_yes_but) / sample_size,3) * 100)))
print("  </tr>\n")

mental_health_keys = ["ASD", "OCD", "AnxietyDisorder", "Schizophrenia"]
for key in mental_health_keys:
    cursor.execute("SELECT count(*) FROM data WHERE " + key + 
                   "='Yes, I was formally diagnosed by a doctor or other mental health professional'" +
                   " AND BasiliskAnxiety NOT NULL;")
    sample_size = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM data WHERE " + key + 
                   "='Yes, I was formally diagnosed by a doctor or other mental health professional'" +
                   " AND BasiliskAnxiety = 'Yes';")
    key_yes_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM data WHERE " + key + 
                   "='Yes, I was formally diagnosed by a doctor or other mental health professional'" +
                   " AND BasiliskAnxiety = 'Yes but only because I worry about everything';")
    key_yes_base_rate_count = cursor.fetchone()[0]
    combined_count = key_yes_count + key_yes_base_rate_count
    print("  <tr>\n")
    print("    <td>{}</td>\n".format(key),
          "    <td>{}%</td>\n".format(str(round(key_yes_count / sample_size,3) * 100)),
          "    <td>{}%</td>\n".format(str(round(key_yes_base_rate_count / sample_size,3) * 100)),
          "    <td>{}%</td>\n".format(str(round(combined_count / sample_size,3) * 100)))
    print("  </tr>\n")
print("</table>")

# Basilisk Belief/Worry and MIRI donation

cursor.execute("SELECT count(*) FROM data WHERE BasiliskCorrectness = 'No';")
no_sample_size = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE BasiliskCorrectness = " +
               "\"Yes but I don't think it's logical conclusions apply for other reasons\";")
yes_but_sample_size = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE BasiliskCorrectness = 'Yes';")
yes_sample_size = cursor.fetchone()[0]

cursor.execute("SELECT sum(CharityDonations_7) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskCorrectness NOT NULL;")
sum_money = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskCorrectness = 'No';")
basilisk_belief_donors_no = cursor.fetchone()[0]

cursor.execute("SELECT sum(CharityDonations_7) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskCorrectness = 'No';")
basilisk_belief_money_no = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskCorrectness = \"Yes but I don't think it's logical conclusions apply for other reasons\";")
basilisk_belief_donors_yes_but = cursor.fetchone()[0]

cursor.execute("SELECT sum(CharityDonations_7) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskCorrectness = \"Yes but I don't think it's logical conclusions apply for other reasons\";")
basilisk_belief_money_yes_but = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskCorrectness = 'Yes';")
basilisk_belief_donors_yes = cursor.fetchone()[0]

cursor.execute("SELECT sum(CharityDonations_7) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskCorrectness = 'Yes';")
basilisk_belief_money_yes = cursor.fetchone()[0]

cursor.execute("SELECT CharityDonations_7 FROM data WHERE CharityDonations_7 > 0" +
              " AND BasiliskCorrectness = 'No';")
no_data = cursor.fetchall()
no_data = [row[0] for row in no_data]

cursor.execute("SELECT CharityDonations_7 FROM data WHERE CharityDonations_7 > 0" +
              " AND BasiliskCorrectness = \"Yes but I don't think it's logical conclusions apply for other reasons\";")
yes_but_data = cursor.fetchall()
yes_but_data = [row[0] for row in yes_but_data]

cursor.execute("SELECT CharityDonations_7 FROM data WHERE CharityDonations_7 > 0" +
              " AND BasiliskCorrectness = 'Yes';")
yes_data = cursor.fetchall()
yes_data = [row[0] for row in yes_data]

print("<table>\n")
print("<caption>Percentage Of People Who Donate To MIRI Versus Basilisk Belief</caption>")
print("<tr>\n",
      "<th>Belief</th>\n",
      "<th>Percentage</th>\n",
      "</tr>\n")
print("<tr>\n",
      "<td>Believe It's Incorrect</td>\n",
      "<td>{}%</td>\n".format(round(basilisk_belief_donors_no / no_sample_size, 3) * 100),
      "</tr>\n")
print("<tr>\n",
      "<td>Believe It's Structurally Correct</td>\n",
      "<td>{}%</td>\n".format(round(basilisk_belief_donors_yes_but / yes_but_sample_size,3) * 100),
      "</tr>\n")
print("<tr>\n",
      "<td>Believe It's Correct</td>\n",
      "<td>{}%</td>\n".format(round(basilisk_belief_donors_yes / yes_sample_size,3) * 100),
      "</tr>\n")
print("</table>\n")

print("<table>\n")
print("<caption>Sum Money Donated To MIRI Versus Basilisk Belief</caption>")
print("<tr>\n",
      "<th>Belief</th>\n",
      "<th>Mean</th>\n",
      "<th>Median</th>\n",
      "<th>Mode</th>\n",
      "<th>Stdev</th>\n",
      "<th>Total Donated</th>\n",
      "</tr>\n")
print("<tr>\n",
      "<td>Believe It's Incorrect</td>\n",
      "<td>{}</td>\n".format(statistics.mean(no_data)),
      "<td>{}</td>\n".format(statistics.median(no_data)),
      "<td>{}</td>\n".format(statistics.mode(no_data)),
      "<td>{}</td>\n".format(statistics.stdev(no_data)),
      "<td>{}</td>\n".format(basilisk_belief_money_no),
      "</tr>\n")
print("<tr>\n",
      "<td>Believe It's Structurally Correct</td>\n",
      "<td>{}</td>\n".format(statistics.mean(yes_but_data)),
      "<td>{}</td>\n".format(statistics.median(yes_but_data)),
      "<td>{}</td>\n".format(statistics.mode(yes_but_data)),
      "<td>{}</td>\n".format(statistics.stdev(yes_but_data)),
      "<td>{}</td>\n".format(basilisk_belief_money_yes_but),
      "</tr>\n")
print("<tr>\n",
      "<td>Believe It's Correct</td>\n",
      "<td>{}</td>\n".format(statistics.mean(yes_data)),
      "<td>{}</td>\n".format(statistics.median(yes_data)),
      "<td>{}</td>\n".format(statistics.mode(yes_data)),
      "<td>{}</td>\n".format(statistics.stdev(yes_data)),
      "<td>{}</td>\n".format(basilisk_belief_money_yes),
      "</tr>\n")
print("</table>\n")



cursor.execute("SELECT count(*) FROM data WHERE BasiliskAnxiety = 'No';")
no_sample_size = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE BasiliskAnxiety = 'Yes but only because I worry about everything';")
yes_but_sample_size = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE BasiliskAnxiety = 'Yes';")
yes_sample_size = cursor.fetchone()[0]

cursor.execute("SELECT sum(CharityDonations_7) FROM data WHERE CharityDonations_7 > 0" + 
               " AND BasiliskAnxiety NOT NULL;")
sum_money = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'No';")
basilisk_donors_no = cursor.fetchone()[0]
cursor.execute("SELECT sum(CharityDonations_7) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'No';")
basilisk_money_no = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'Yes';")
basilisk_donors_yes = cursor.fetchone()[0]
cursor.execute("SELECT sum(CharityDonations_7) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'Yes';")
basilisk_money_yes = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'Yes but only because I worry about everything';")
basilisk_donors_yes_but = cursor.fetchone()[0]
cursor.execute("SELECT sum(CharityDonations_7) FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'Yes but only because I worry about everything';")
basilisk_money_yes_but = cursor.fetchone()[0]


combined_donors = basilisk_donors_yes + basilisk_donors_yes_but
combined_money = basilisk_money_yes + basilisk_money_yes_but

cursor.execute("SELECT CharityDonations_7 FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'No';")
no_data = cursor.fetchall()
no_data = [row[0] for row in no_data]

cursor.execute("SELECT CharityDonations_7 FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'Yes but only because I worry about everything';")
yes_but_data = cursor.fetchall()
yes_but_data = [row[0] for row in yes_but_data]

cursor.execute("SELECT CharityDonations_7 FROM data WHERE CharityDonations_7 > 0" +
               " AND BasiliskAnxiety = 'Yes';")
yes_data = cursor.fetchall()
yes_data = [row[0] for row in yes_data]

print("<table>\n")
print("<caption>Percentage Of People Who Donate To MIRI Versus Basilisk Worry</caption>\n")
print("<tr>\n",
      "<th>Anxiety</th>\n",
      "<th>Percentage</th>\n",
      "</tr>\n")
print("<tr>\n",
      "<td>Never Worried</td>\n",
      "<td>{}%</td>\n".format(round(basilisk_donors_no / no_sample_size,3) * 100),
      "</tr>\n")
print("<tr>\n",
      "<td>Worried But They Worry About Everything</td>\n",
      "<td>{}%</td>\n".format(round(basilisk_donors_yes_but / yes_but_sample_size,3) * 100),
      "</tr>\n")
print("<tr>\n",
      "<td>Worried</td>\n",
      "<td>{}%</td>\n".format(round(basilisk_donors_yes / yes_sample_size,3) * 100),
      "</tr>\n")
print("<tr>\n",
      "<td>Combined Worry</td>\n",
      "<td>{}%</td>\n".format(round(combined_donors / 
                                    (yes_but_sample_size + yes_sample_size),
                                    3) * 100),
      "</tr>\n")
print("</table>\n")

print("<table>\n")
print("<caption>Sum Money Donated To MIRI Versus Basilisk Worry</caption>\n")
print("<tr>\n",
      "<th>Anxiety</th>\n",
      "<th>Mean</th>\n",
      "<th>Median</th>\n",
      "<th>Mode</th>\n",
      "<th>Stdev</th>\n",
      "<th>Total Donated</th>\n",
      "</tr>\n")
print("<tr>\n",
      "<td>Never Worried</td>\n",
      "<td>{}</td>\n".format(statistics.mean(no_data)),
      "<td>{}</td>\n".format(statistics.median(no_data)),
      "<td>{}</td>\n".format(statistics.mode(no_data)),
      "<td>{}</td>\n".format(statistics.stdev(no_data)),
      "<td>{}</td>\n".format(basilisk_money_no),
      "</tr>\n")
print("<tr>\n",
      "<td>Worried But They Worry About Everything</td>\n",
      "<td>{}</td>\n".format(statistics.mean(yes_but_data)),
      "<td>{}</td>\n".format(statistics.median(yes_but_data)),
      "<td>{}</td>\n".format(statistics.mode(yes_but_data)),
      "<td>{}</td>\n".format(statistics.stdev(yes_but_data)),
      "<td>{}</td>\n".format(basilisk_money_yes_but),
      "</tr>\n")
print("<tr>\n",
      "<td>Worried</td>\n",
      "<td>{}</td>\n".format(statistics.mean(yes_data)),
      "<td>{}</td>\n".format(statistics.median(yes_data)),
      "<td>{}</td>\n".format(statistics.mode(yes_data)),
      "<td>{}</td>\n".format(statistics.stdev(yes_data)),
      "<td>{}</td>\n".format(basilisk_money_yes),
      "</tr>\n")
print("<tr>\n",
      "<td>Combined Worry</td>\n",
      "<td></td>\n",
      "<td></td>\n",
      "<td></td>\n",
      "<td></td>\n",
      "<td>{}</td>\n".format(combined_money),
      "</tr>\n")
print("</table>\n")
