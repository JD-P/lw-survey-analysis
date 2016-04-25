from operator import add
import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="The filepath to the db file to analyze.")
parser.add_argument("-s", "--sanity", action="store_true", 
                    help="Sanity check figures such as total donated to charity.")
arguments = parser.parse_args()

db_conn = sqlite3.connect(arguments.filepath)
cursor = db_conn.cursor()
keys = ['EAKnowledge', 'EAIdentity', 'EACommunity', 'EADonations',
'EAAnxiety', 'EAOpinion', 'Income', 'IncomeCharityPortion', 'XriskCharity', 
'CharityDonations_1', 'CharityDonations_2', 'CharityDonations_3', 'CharityDonations_4', 
'CharityDonations_5', 'CharityDonations_6', 'CharityDonations_7', 'CharityDonations_8',
'CharityDonations_9', 'CharityDonations_10','CharityDonations_11','CharityDonations_12',
'CharityDonations_13', 'CharityDonations_14','CharityDonations_15','Vegetarian']

cursor.execute("select " + ",".join(keys) + " from data;")
rows = cursor.fetchall()
# Calculate total amount of money donated to charity
# If somebody lists their IncomeCharityPortion, skip further probing, otherwise tally
# individual charity contributions.
income_total = 0
charity_total = 0
for row in rows:
    if row[6]:
        income_total += row[6]
    elif row[7]:
        income_total += row[7]
    else:
        for charity in row[8:24]:
            if charity:
                income_total += charity
    if row[7]:
        charity_total += row[7]
    else:
        for charity in row[8:24]:
            if charity:
                charity_total += charity
print("Total income of survey participants:", income_total)
print("Total amount of money donated to charity by survey participants:", charity_total)
print("Relative portion of money donated to charity by survey participants:", charity_total / income_total)

# Donation statistics by political affiliation
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
    cursor.execute("select " + ",".join(keys) 
                   + " from data where ComplexAffiliation == ?;", (affiliation,))
    affil_rows = cursor.fetchall()
    affil_income = 0
    affil_charity = 0
    for row in affil_rows:
        if row[6]:
            affil_income += row[6]
        elif row[7]:
            affil_income += row[7]
        else:
            for charity in row[8:24]:
                if charity:
                    affil_income += charity
        if row[7]:
            affil_charity += row[7]
        else:
            for charity in row[8:24]:
                if charity:
                    affil_charity += charity
    print("\n")
    print("Sample size:", len(affil_rows)) # Naive sample size
    # ^ A better version would only count those members who actually answered the
    # charity section.
    print("Total income for political affiliation '" + affiliation + "':", affil_income)
    print("Total charity contributions for political affiliation '" 
          + affiliation + "':", affil_charity)
    print("Percentage of income donated to charity:", affil_charity / affil_income)
    print("Portion of total charity contributions for all survey respondents:",
          affil_charity / charity_total)
#Sanity checking the above figures, if sanity check flag is on
if arguments.sanity:
    # We start by creating lists of the values in each column which we can perform
    # generic operations on
    columns = [list() for i in range(18)]
    for row in rows:
        if row[6]:
            columns[0].append(row[6])
        if row[7]:
            columns[1].append(row[7])
        for charity in enumerate(row[8:24]):
            if charity[1]:
                columns[charity[0] + 2].append(charity[1])
    for column in columns:
        column.sort()
        print(max(column))
    # A bit of accounting to see who says they donated more than their income or their
    # portion donated to charity.
    # And how much money is involved in that.
    fishy = 0
    money_involved = 0
    for row in rows:
        if row[6] and row[7]:
            if row[7] > row[6]:
                fishy += 1
                money_involved += sum([row[7]] + 
                                      [charity for charity in row[8:24] if charity])
                continue
        elif row[7]:
            if sum([charity for charity in row[8:24] if charity]) > row[7]:
                fishy += 1
                money_involved += sum([row[7]] + 
                                      [charity for charity in row[8:24] if charity])
    print("Respondents who donated more than their income or charity portion:", fishy)
    print("How much money is in this category:", money_involved)
print("\n\nEffective Altruism:\n")

# Effective Altruism Statistics

# How much money donated
cursor.execute("select " + ','.join(keys) + " from data where EAIdentity=?;",
               ["Yes"])
rows = cursor.fetchall()
# Calculate total amount of money donated to charity
# If somebody lists their IncomeCharityPortion, skip further probing, otherwise tally
# individual charity contributions.
income_total = 0
charity_total = 0
for row in rows:
    if row[6]:
        income_total += row[6]
    elif row[7]:
        income_total += row[7]
    else:
        for charity in row[8:24]:
            if charity:
                income_total += charity
    if row[7]:
        charity_total += row[7]
    else:
        for charity in row[8:24]:
            if charity:
                charity_total += charity
print("Total EA respondents:", len(rows))
print("Total income of EA participants:", income_total)
print("Total amount of money donated to charity by EA participants:", charity_total)
print("Relative portion of income donated to charity by EA participants:", 
      charity_total / income_total, end="\n\n")
# EA effectiveness
print("EA Effectiveness:", end="\n\n")
cursor.execute('select count(EADonations) from data where EADonations !="N/A";')
total_EA_donation_respondents = cursor.fetchone()[0]
cursor.execute('select count(EADonations) from data where EADonations="Yes"');
total_new_donations = cursor.fetchone()[0]
print("Percentage of respondents who made new donations as a result of EA:",
      total_new_donations / total_EA_donation_respondents)
total_EAs = len(rows)
cursor.execute('select count(EADonations) from data where EAIdentity="Yes" ' + 
               'AND EADonations="Yes";')
ea_new_donations = cursor.fetchone()[0]
print("Percentage of EA respondents who made new donations as a result of EA:",
      ea_new_donations / total_EAs, end="\n\n")

# Anxiety versus donations
cursor.execute('select ' + ','.join(keys) + ' from data where ' +
               'EAIdentity="No" AND EAAnxiety="Yes";')
anxious_rows = cursor.fetchall()
cursor.execute('select ' + ','.join(keys) + ' from data where ' +
               'EAIdentity="No" AND EAAnxiety="No";')
calm_rows = cursor.fetchall()

def calc_donations(rows, indices):
    """Calculate the total amount of money donated in <rows> to the charities 
    indicated by <indices>.

    rows is a list of rows taken from the database.
    indices is a list of the fields to take from each row of the rows.

    returns a dictionary of indices and their donation totals"""
    indice_dict = {}.fromkeys(indices, 0)
    for row in rows:
        for indice in indices:
            if row[indice]:
                indice_dict[indice] += row[indice]
    return indice_dict

indices = list(range(9,24))
anxious_donations = calc_donations(anxious_rows,indices)
calm_donations = calc_donations(calm_rows,indices)

anxious_donation_total = sum(anxious_donations.values())
print("Sample Size:", len(anxious_rows))
print("Average amount of money donated by people anxious about EA who aren't EAs:", 
      anxious_donation_total / len(anxious_rows))
calm_donation_total = sum(calm_donations.values())
print("Sample Size:", len(calm_rows))
print("Average amount of money donated by people who aren't anxious about EA " +
      "who aren't EAs:",
      calm_donation_total / len(calm_rows), end="\n\n")

cursor.execute('select ' + ','.join(keys) + ' from data where ' + 
               'EAIdentity="Yes" AND EAAnxiety="Yes";')
EA_anxious_rows = cursor.fetchall()
cursor.execute('select ' + ','.join(keys) + ' from data where ' +
               'EAIdentity="Yes" AND EAAnxiety="No";')
EA_calm_rows = cursor.fetchall()
EA_anxious_donations = calc_donations(EA_anxious_rows, indices)
EA_calm_donations = calc_donations(EA_calm_rows, indices)

EA_anxious_donation_total = sum(EA_anxious_donations.values())
print("Sample Size:", len(EA_anxious_rows))
print("Average amount of money donated by EAs anxious about EA:",
      EA_anxious_donation_total / len(EA_anxious_rows))
EA_calm_donation_total = sum(EA_calm_donations.values())
print("Sample Size:", len(EA_calm_rows))
print("Average amount of money donated by EAs not anxious about EA:",
      EA_calm_donation_total / len(EA_calm_rows),end="\n\n")

# Probability of EA given anxiety
cursor.execute("select count(*) from data where EAAnxiety is not null;")
total_respondents = cursor.fetchone()[0]
cursor.execute('select count(*) from data where EAIdentity="Yes";')
total_EAs = cursor.fetchone()[0]
cursor.execute('select count(*) from data where EAAnxiety="Yes";')
total_EA_anxiety = cursor.fetchone()[0]
cursor.execute('select count(*) from data where EAIdentity="Yes" AND EAAnxiety="Yes";')
EA_EA_anxiety = cursor.fetchone()[0]
cursor.execute('select count(*) from data where EAIdentity="No" AND EAAnxiety="Yes";')
EA_calm = cursor.fetchone()[0]
P_ea_given_anxiety = (((EA_EA_anxiety / total_EAs) * (total_EAs / total_respondents)) 
                      / (total_EA_anxiety / total_respondents))
print("Sample Size:", total_respondents)
print("P(Effective Altruist):", total_EAs / total_respondents)
print("P(EA Anxiety):", total_EA_anxiety / total_respondents)
print("P(Effective Altruist | EA Anxiety):", P_ea_given_anxiety, end="\n\n")

givewell_charities_indices = [9,10,11,12]
givewell_charities_donations = calc_donations(rows, givewell_charities_indices)
givewell_charities_total = sum(givewell_charities_donations.values())
print("Amount of EA money sent to top four GiveWell charities:", 
      givewell_charities_total)
charity_labels = {9:"Against Malaria Foundation",
                  10:"Schistosomiasis Control Initiative",
                  11:"Deworm the World Initiative",
                  12:"GiveDirectly"}
print("Breakdown By Charity:", end="\n\n")
for indice in sorted(givewell_charities_donations.keys()):
    print(charity_labels[indice] + ":", givewell_charities_donations[indice])
print("\n")

miri_cfar_indices = [15,18]
miri_cfar_donations = calc_donations(rows, miri_cfar_indices)
miri_cfar_total = sum(miri_cfar_donations.values())
print("Amount of EA money sent to MIRI and CFAR:", miri_cfar_total)
charity_labels = {15:"Machine Intelligence Research Institute",
                  18:"Center For Applied Rationality"}
print("Breakdown By Charity:", end="\n\n")
for indice in sorted(miri_cfar_donations.keys()):
    print(charity_labels[indice] + ":", miri_cfar_donations[indice])

# EA versus communities
# EA versus political affiliation
# EA and Xrisk
