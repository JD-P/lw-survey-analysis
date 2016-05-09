# coding: utf-8

#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                    Version 2, December 2004

# Copyright (C) 2016 Anonymous <sam@hocevar.net>

# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.


#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

 # 0. You just DO WHAT THE FUCK YOU WANT TO.


# LessWrong 2016 Survey: Mental Disorders

from __future__ import division

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="The filepath to read the CSV from.")
parser.add_argument("output", help="The directory to save the output images to.")
arguments = parser.parse_args()

mpl.rcParams['font.size'] = 22
mpl.rcParams['figure.titlesize'] = 34
mpl.rcParams['figure.titleweight'] = 'bold'


survey = pd.read_csv(arguments.filepath, low_memory=False)

community_names = ['LessWrong',
                   'LessWrong Meetups',
                   'LessWrong Facebook Group',
                   'LessWrong Slack',
                   'SlateStarCodex',
                   'Rationalist Tumblr',
                   'Rationalist Facebook',
                   'Rationalist Twitter',
                   'Effective Altruism Hub',
                   'FortForecast',
                   'Good Judgement(TM) Open',
                   'PredictionBook',
                   'Omnilibrium',
                   'Hacker News',
                   '#lesswrong on freenode',
                   '#slatestarcodex on freenode',
                   '#hplusroadmap on freenode',
                   '#chapelperilous on freenode',
                   '/r/rational',
                   '/r/HPMOR',
                   '/r/SlateStarCodex',
                   "One or more private 'rationalist' groups"]

communities = list(zip(['ActiveMemberships[{}]'.format(n) for n in range(1, 23)], community_names))
survey['Overall'] = 'Yes'  # hack. TODO: rewrite hack
communities += [('Overall', 'Overall')]

disorders = ['Depression',
             'OCD',
             'ASD',
             'ADHD',
             'BipolarDisorder',
             'AnxietyDisorder',
             'BPD',
             'Schizophrenia',
             'SubstanceUseDisorder']


def community_disorders(disorder):
    df = pd.DataFrame(columns=['Community', 'Formal diagnosis', 'Self-diagnosis'])

    for key, name in communities:
        counts = survey.loc[survey[key] == 'Yes'][disorder].value_counts()
        size = counts.sum()

        try:
            self_percent = counts['Not formally, but I personally believe I have (or had) it'] / size
        except KeyError:
            self_percent = 0

        try:
            formal_percent = counts['Yes, I was formally diagnosed by a doctor or other mental health professional'] / size
        except KeyError:
            formal_percent = 0

        row = {'Community': '{name} (Size: {size})'.format(name=name, size=size),
               'Self-diagnosis': self_percent,
               'Formal diagnosis': formal_percent}

        df = df.append(row, ignore_index=True)

    fig, ax = plt.subplots(1, 1, figsize=(25, 10))
    
    bars = df.plot.bar(stacked=True, ax=ax, width=0.7, color=['#66a1dd', '#d0e1f4'], edgecolor='none')
    bars.patches[22].set_color('#89a14c')  # yep, hard-coding the indices
    bars.patches[45].set_color('#dee8c9')  # whoop
    
    ax.set_xticklabels(df['Community'], rotation=45, ha='right')
    yticks = ax.get_yticks()
    ax.set_yticklabels(['{percent:.0f}%'.format(percent=ytick * 100) for ytick in yticks], fontname='Georgia')
    ax.tick_params(axis='both', which='both', length=0)
    
    for spine in ax.spines.values():
        spine.set_color('#666666')
    ax.spines['right'].set_color('none')
    
    ax.grid(axis='y', linestyle='-', color='#666666')
    ax.set_axisbelow(True)
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False)
    
    fig.suptitle('Reported {disorder} Prevalence by Rationalist Community'.format(disorder=disorder))

    fig.savefig(os.path.join(arguments.output + '{}'.format(disorder)), bbox_inches='tight')


# community_disorders('Depression')  # with dicked data

# survey.Age = pd.to_numeric(survey.Age, errors='coerce')
# survey[(survey.Age < 10) | (survey.Age > 90)] = np.nan

# survey.IQ = pd.to_numeric(survey.IQ, errors='coerce')
# survey[(survey.IQ < 70) | (survey.IQ > 200)] = np.nan

# survey.SingularityYear = pd.to_numeric(survey.SingularityYear, errors='coerce')
# survey[(survey.SingularityYear < 2016) | (survey.SingularityYear > 4000)] = np.nan

# survey.UnemploymentYear = pd.to_numeric(survey.UnemploymentYear, errors='coerce')
# survey[(survey.UnemploymentYear < 2016) | (survey.UnemploymentYear > 4000)] = np.nan

for disorder in disorders:
    community_disorders(disorder)
