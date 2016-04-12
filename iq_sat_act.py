from email.utils import parseaddr
import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="Filepath to the db file to analyze.")
parser.add_argument("-f", "--floor", type=int, default=65, 
                    help="The floor at which to exclude a score from consideration.")
parser.add_argument("-c", "--ceiling", type=int, default=250, 
                    help="The ceiling at which to exclude a score from consideration.")
arguments = parser.parse_args()

db_conn = sqlite3.connect(arguments.filepath)
cursor = db_conn.cursor()

keys = ['IQ', 'IQAge', 'IQType', 'SAT', 'SAT2', 'ACT']

cursor.execute("select " + ",".join(keys) + " from data where IQ;")
iq_accum = 0 # Accumulator to calculate average
num_scores = 0 # We want to not count people who are excluded
non_multiples_of_five = 0
nmof_scores = 0
rows = cursor.fetchall()
for row in rows:
    if arguments.floor < row[0] < arguments.ceiling:
        iq_accum += row[0]
        num_scores += 1
        if row[0] % 5:
            non_multiples_of_five += row[0]
            nmof_scores += 1
average_iq = iq_accum / num_scores
nmof_average = non_multiples_of_five / nmof_scores
print("Number of respondents who provided an IQ score:", num_scores)
print("Average IQ:", average_iq)
print("Number of respondents who provided an IQ score that wasn't a multiple of five:", 
      nmof_scores)
print("Average IQ among those whose IQ isn't a multiple of five:", nmof_average)

# By special request, average IQ for every major email provider
# Turns out we don't really have a sample size large enough to get useful results
# from this.
cursor.execute("select EmailAddress, IQ from data where IQ;")
email_addrs = [(row[0],row[1]) for row in cursor.fetchall() if row[0]]
providers = {}
for address in email_addrs:
    if parseaddr(address[0]) != ('',''):
        try:
            provider = address[0].split("@")[1]
        except IndexError:
            continue
        if provider in providers:
            providers[provider][0] += 1
            providers[provider][1] += address[1]
        else:
            providers[provider] = [1, address[1]]
provider_list = []
for provider in providers:
    provider_list.append(providers[provider] + [provider])
provider_list.sort()
for provider in provider_list:
    if provider[0] > 25:
        provider_iq = provider[1] / provider[0]
        provider_users = provider[0]
        print("\n")
        print("Number of " + provider[2] + " users:", provider_users)
        print(provider[2] + " users average IQ (given LessWronger):", provider_iq)
        
    
