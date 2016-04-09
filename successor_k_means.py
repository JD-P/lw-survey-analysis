import sqlite3
from scipy.cluster import vq
from numpy import array 
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="Filepath to the input file db file.")
parser.add_argument("-o", "--output", help="Filepath to write the output to.")
parser.add_argument("-k", default=6, type=int, help="The number of clusters.")
arguments = parser.parse_args()

db_conn = sqlite3.connect(arguments.filepath)
cursor = db_conn.cursor()
cursor.execute("select SuccessorPhilosophy_1, SuccessorPhilosophy_2, " 
               + "SuccessorPhilosophy_3, SuccessorPhilosophy_4, " +
               "SuccessorPhilosophy_5, SuccessorCommunity_1, " +
               "SuccessorCommunity_2, SuccessorCommunity_3, " +
               "SuccessorCommunity_4, SuccessorCommunity_5 from data" +
               " WHERE SuccessorPhilosophy_1 NOT NULL OR SuccessorPhilosophy_2 "
               + "NOT NULL OR SuccessorPhilosophy_3 NOT NULL OR " + 
               "SuccessorPhilosophy_4 NOT NULL OR SuccessorPhilosophy_5 NOT " +
               "NULL OR SuccessorCommunity_1 NOT NULL OR " +
               "SuccessorCommunity_2 NOT NULL OR SuccessorCommunity_3 NOT NULL "
               + "OR SuccessorCommunity_4 NOT NULL OR SuccessorCommunity_5;")
observations = cursor.fetchall()
cursor.close()

for observation in enumerate(observations):
    observations[observation[0]] = array(
        [{None:0, 'More':1, 'Same':2, 'Less':3}[choice] 
         for choice in observation[1]]
    )
observations = array(observations)

K = arguments.k
clusters = {}
for i in range(K):
    clusters[i] = []
kmeans_indexes = vq.vq(observations, vq.kmeans(observations, K)[0])[0]
for index in enumerate(kmeans_indexes):
    clusters[index[1]].append(observations[index[0]])

questions = ["Attention Paid To Outside Sources",
             "Self Improvement Focus",
             "AI Focus",
             "Political",
             "Academic/Formal",
             "Intense Environment",
             "Focused On 'Real World' Action",
             "Experts",
             "Data Driven/Testing Of Ideas",
             "Social"]
grids = []
for centroid in range(K):
    answer_grid = [list((0,0,0,0,questions[i])) for i in range(10)]
    for observation in clusters[centroid]:
        for choice in enumerate(observation):
            answer_grid[choice[0]][choice[1]] += 1
    grids.append((len(clusters[centroid]), answer_grid))
grids.sort()
for grid in grids:
    print("Cluster Size: " + str(grid[0]))
    for row in grid[1]:
        print(row)
    print("----")
    


