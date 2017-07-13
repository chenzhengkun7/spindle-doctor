# coding=UTF-8
import sys
import logging
import glob
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

mpl.rcParams['agg.path.chunksize'] = 10000

SRC_DIR = u'../../build/data/labeled'
DEST_DIR = u'../../build/plots/feature-observation'
INPUT_CSV_COLUMNS = [
    'timestamp', 'yyyy', 'MM', 'dd', 'hh', 'mm', 'ss', 'fff',
    'x', 'y', 'z',
    'uInG', 'vInG', 'wInG',
    'rul',
    'ss_acc',
    'ss_curr',
    'ss_acc_normal',
    'ss_curr_normal',
]
CONFIG_MAP = {
    'default': {
        'marker': {
            'linewidth': 0,
            'marker': '.',
            'markersize': 1,
            'color': 'blue',
            'alpha': 0.5,
            'zorder': 10,
        },
        # 'ylim': [-0.8, 0.8],
    },
    'x': {
        'marker': {
            'color': 'red',
            # 'linewidth': 1,
            # 'markersize': 3,
        },
        'ylim': [-5000, 5000],
        'label': 'Accelerometer Reading (mg)',
    },
    'y': {
        'marker': {
            'color': 'green',
        },
        'ylim': [-5000, 5000],
        'label': 'Accelerometer Reading (mg)',
    },
    'z': {
        'marker': {
            'color': 'blue',
        },
        'ylim': [-5000, 5000],
        'label': 'Accelerometer Reading (mg)',
    },
    'uInG': {
        'marker': {
            'color': 'red',
        },
        'ylim': [-0.03, 0.03],
        'label': 'U Phase Current (A)',
    },
    'vInG': {
        'marker': {
            'color': 'green',
        },
        'ylim': [-0.03, 0.03],
        'label': 'V Phase Current (A)',
    },
    'wInG': {
        'marker': {
            'color': 'blue',
        },
        'ylim': [-0.03, 0.03],
        'label': 'W Phase Current (A)',
    },
    'ss_acc': {
        'marker': {
            'color': 'blue',
        },
        'ylim': [0, 30000000],
        'label': 'ss_acc',
    },
    'ss_curr': {
        'marker': {
            'color': 'blue',
        },
        'ylim': [0, 0.002],
        'label': 'ss_curr',
    },
    'ss_acc_normal': {
        'marker': {
            'color': 'blue',
        },
        'ylim': [-1, 1.2],
        'label': 'ss_acc_normal',
    },
    'ss_curr_normal': {
        'marker': {
            'color': 'blue',
        },
        'ylim': [-1, 1.2],
        'label': 'ss_curr_normal',
    },
    'x_diff': {
        'marker': {
            'color': 'blue',
            'linewidth': 1,
            'markersize': 3,
        },
        'ylim': [-500, 500],
        'label': 'x_diff',
    },
    'x_abs_diff': {
        'marker': {
            'color': 'blue',
            'linewidth': 1,
            'markersize': 3,
        },
        'ylim': [-500, 500],
        'label': 'x_abs_diff',
    },
}
FEATURE_PLOTS = {
    'M1': ['x'],
    'M2': ['y'],
    'M3': ['z'],
    'M4': ['x', 'y', 'z'],
    'M5': ['uInG'],
    'M6': ['vInG'],
    'M7': ['wInG'],
    'M8': ['uInG', 'vInG', 'wInG'],
    'M9': ['ss_acc'],
    'M10': ['ss_curr'],
    'M11': ['ss_acc_normal'],
    'M12': ['ss_curr_normal'],
    'M13': ['x', 'x_diff'],
    'M14': ['x_abs_diff'],
}

def toMillisecond(rowOrDataframe):
    return (
        (
            rowOrDataframe['hh'] * 3600 +
            rowOrDataframe['mm'] * 60 +
            rowOrDataframe['ss']
        ) * 1000 +
        rowOrDataframe['fff']
    )

def plot(df, dataset, filename):
    for featurePlot in FEATURE_PLOTS:
        featureNames = FEATURE_PLOTS[featurePlot]
        lines = ()
        labels = ()
        axisOffset = 1
        fig, ax = plt.subplots()
        ax.yaxis.set_visible(False)
        ax.patch.set_visible(False)
        ax.set_xlabel('Time (ms)')

        for featureName in featureNames:
            axFeature = ax.twinx()
            marker = dict(
                CONFIG_MAP['default']['marker'].items() +
                CONFIG_MAP[featureName]['marker'].items()
            )
            configs = dict(
                CONFIG_MAP['default'].items() +
                CONFIG_MAP[featureName].items()
            )

            new_fixed_axis = axFeature.spines['right'].set_position(('axes', axisOffset))
            axisOffset += 0.2
            axFeature.yaxis.tick_right()
            axFeature.set_xlim(
                df['millisecond'].min(),
                df['millisecond'].max() + (
                    (
                        df['millisecond'].max() -
                        df['millisecond'].min()
                    ) *
                    0.1
                )
            )
            axFeature.set_ylim(configs['ylim'])
            axFeature.set_ylabel(configs['label'], color=marker['color'])
            axFeature.tick_params('y', colors=marker['color'])

            lineFeature, = axFeature.plot(
                df['millisecond'],
                df[featureName],
                **marker
            )
            lines += (lineFeature,)
            labels += (featureName,)

        fig.tight_layout()

        # output figure
        destDir = os.path.join(DEST_DIR, dataset, featurePlot)
        if not os.path.exists(destDir):
            os.makedirs(destDir)
        title = '{0}_{1}'.format(
            os.path.basename(filename),
            '+'.join(featureNames)
        )
        plt.title(title)
        plt.legend(lines, labels, loc='upper left')
        plt.savefig(
            os.path.join(destDir, '{0}.jpg'.format(title)),
            dpi=400,
            format='jpg'
        )
        plt.clf()

def main():
    datasets = os.listdir(SRC_DIR)
    for dataset in datasets:
        filenames = glob.glob(os.path.join(SRC_DIR, dataset, '*.csv'))
        for fileFullName in filenames:
            filename = os.path.basename(fileFullName)
            print('reading ' + filename + '...')

            df = pd.read_csv(
                fileFullName,
                sep=',',
                header=None,
                names=INPUT_CSV_COLUMNS
            )
            offset = toMillisecond(df.iloc[0])
            df['millisecond'] = toMillisecond(df) - offset
            # df['millisecond'] = df['millisecond'][30000:30100]
            df['x_diff'] = df['x'].diff()
            df['x_abs_diff'] = df['x'].abs().diff()
            plot(df, dataset, filename)

main()