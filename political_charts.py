#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
# 0. You just DO WHAT THE FUCK YOU WANT TO.

from __future__ import division

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('filepath', help='The filepath to read the CSV from.')
parser.add_argument('output', help='The directory to save the output images to.')
arguments = parser.parse_args()

mpl.rcParams['font.size'] = 22
mpl.rcParams['figure.titlesize'] = 34
mpl.rcParams['legend.fontsize'] = 20
mpl.rcParams['xtick.direction'] = 'out'


survey = pd.read_csv(arguments.filepath, low_memory=False)


# seriously now...
issues = {
    'AbortionLaws[SQ001]': {
        'label': 'Liberal Abortion Laws',
        'likert': {
                0: 'Pro-Life',
                1: 'Lean Pro-Life',
                2: 'No strong opinion',
                3: 'Lean Pro-Choice',
                4: 'Pro-Choice',
            }
        },
    'Immigration[SQ001]': {
        'label': 'More Immigration',
        'likert': {
                0: 'Should be more restricted',
                1: 'Lean more restricted',
                2: 'No strong opinion',
                3: 'Lean more open',
                4: 'Should be more open'
            }
        },
    'Taxes[SQ001]': {
        'label': 'Higher Taxes',
        'likert': {
                0: 'Should be lower',
                1: 'Lean towards lower',
                2: 'No strong opinion',
                3: 'Lean towards higher',
                4: 'Should be higher'
            }
        },
    'MinimumWage[SQ001]': {
        'label': 'Higher Minimum Wage',
        'likert': {
                0: 'Should be lower or eliminated',
                1: 'Lean towards lower or eliminated',
                2: 'No strong opinion',
                3: 'Lean towards higher',
                4: 'Should be higher'
            }
        },
    'Feminism[SQ001]': {
        'label': 'Feminism',
        'likert': {
                0: 'Very unfavorable',
                1: 'Unfavorable',
                2: 'No strong opinion',
                3: 'Favorable',
                4: 'Very favorable'
            }
        },
    'SocialJustice[SQ001]': {
        'label': 'Social Justice',
        'likert': {
                0: 'Very unfavorable',
                1: 'Unfavorable',
                2: 'No strong opinion',
                3: 'Favorable',
                4: 'Very favorable'
            }
        },
    'HumanBiodiversity[SQ001]': {
        'label': 'Human Biodiversity',
        'likert': {
                0: 'Very unfavorable',
                1: 'Unfavorable',
                2: 'No strong opinion',
                3: 'Favorable',
                4: 'Very favorable'
            }
        },
    'BasicIncome[SQ001]': {
        'label': 'Basic Income',
        'likert': {
                0: 'Strongly oppose',
                1: 'Oppose',
                2: 'No strong opinion',
                3: 'Support',
                4: 'Strongly support'
            }
        },
    'GreatStagnation[SQ001]': {
        'label': 'Entering Great Stagnation',
        'likert': {
                0: 'Strongly doubt',
                1: 'Doubt',
                2: 'No strong opinion',
                3: 'Believe',
                4: 'Strongly believe'
            }
        }
}

affiliations = [
    'Overall',
    'Left-Libertarian',
    'Social Democrat',
    'Progressive',
    'Libertarian',
    'Other',
    'Pragmatist',
    'Socialist',
    'Moderate',
    'Anarchist',
    'Conservative',
    'Futarchist',
    'Neoreactionary',
    'Communist',
    'Objectivist',
    'Fascist',
    'Monarchist',
    'Totalitarian'
]


def normalize_likert(key, affiliation=None):
    if affiliation is None or affiliation is 'Overall':
        percentages = survey[key].value_counts(normalize=True)
    else:
        percentages = survey[survey.ComplexAffiliation == affiliation][key].value_counts(normalize=True)
    row = pd.Series([percentages.get(issues[key]['likert'][i], 0) for i in range(5)], index=range(5))
    return row


def plot_issues(affiliation=None):
    d = {issues[key]['label']: normalize_likert(key, affiliation=affiliation) for key in issues}
    df = pd.DataFrame(d).transpose()
    df[[0, 1]] *= -1

    fig = plt.figure(figsize=(25, 10))
    gs = gridspec.GridSpec(1, 2, width_ratios=[5, 2])

    ax1 = plt.subplot(gs[0])
    ax2 = plt.subplot(gs[1])
    ax2.set_xlim(0, 0.6)

    barh_kwargs = {
        'sharey': True,
        'stacked': True,
        'edgecolor': 'none',
        'width': 0.8
    }
    ax1colors = ['#f4d1d0', '#df7464', '#d0e1f4', '#66a1dd']
    df.plot.barh(y=[1, 0, 3, 4], ax=ax1, color=ax1colors, **barh_kwargs)
    df.plot.barh(y=2, ax=ax2, color=['#cccccc'], **barh_kwargs)

    legend_kwargs = {
        'loc': 'upper center',
        'bbox_to_anchor': (0, 0, 1, 0),
        'frameon': False
    }
    ax1.legend(['Disagree', 'Strongly Disagree', 'Agree', 'Strongly Agree'], ncol=2, **legend_kwargs)
    ax2.legend(['Neutral'], **legend_kwargs)

    ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    for ax in [ax1, ax2]:
        xticks = ax.get_xticks()
        ax.set_xticklabels(['{:.3g}%'.format(abs(xtick) * 100) for xtick in xticks], fontsize=18)
        ax.xaxis.set_tick_params(labeltop='on', size=10, width=1)
        ax.xaxis.set_ticks_position('top')
        ax.yaxis.set_ticks_position('none')

    ax1.axvline(0, linestyle='-', color='#ffffff', linewidth=3)

    fig.suptitle('Opinions on Political Issues: {}'.format(affiliation), color='#555555')
    fig.tight_layout()
    fig.subplots_adjust(top=0.87)

    fig.savefig(os.path.join(arguments.output + '{}'.format(affiliation)), bbox_inches='tight')


for affiliation in affiliations:
    plot_issues(affiliation)
