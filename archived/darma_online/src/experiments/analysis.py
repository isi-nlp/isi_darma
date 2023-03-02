import os.path
import time
from datetime import datetime

import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import cohen_kappa_score
from scipy.stats import pearsonr
from scipy.stats import spearmanr
from scipy.stats import kendalltau
from darma_online.pipeline.moderation_classifiers import PerspectiveAPIModerator
from darma_online.logging_setup import setup_logger
from darma_online.utils import load_config

MODERATOR_KEY = 'moderator_score'
PERSPECTIVE_KEY = 'perspec_tox_score'
BEHAV_TYPE = 'det_behav_type'
NAMECALLING = 'namecalling'
ADHOMINEM = 'ad_hominem_attacking'
OBSCENE = 'obscene_vulgar'
DEHUMANIZING = 'dehumanizing'

def run(csv_name, plot=True):

    df = pd.read_csv(f'{csv_name}.csv', index_col=0)

    if plot:
        if not os.path.exists(f'plots/{csv_name}'):
            os.makedirs(f'plots/{csv_name}')

        path = f'plots/{csv_name}'
        print(f"Performing analysis on {csv_name} with {df.shape[0]} comments")

        # Joint plot of toxicity scores
        sns.jointplot(x=df[MODERATOR_KEY], y=df[PERSPECTIVE_KEY] )
        plt.savefig(f'{path}/joint_plot.png')

        # Data distribution of the perspective score column and save the plot
        sns.displot(df[PERSPECTIVE_KEY])
        plt.title(f'Perspective Score for {df.shape[0]} comments ({csv_name})')
        plt.savefig(f'{path}/perspective_score_dist.png')

        # Plot distribution of all behavior types scores
        behavior_types = [NAMECALLING, ADHOMINEM, OBSCENE, DEHUMANIZING]
        for behavior in behavior_types:
            sns.displot(df[behavior])
            plt.title(f'{behavior} Dist for {df.shape[0]} comments ({csv_name})')
            plt.savefig(f'{path}/{behavior}_score_dist.png')

        # Data distribution of the moderator score column and save the plot
        sns.displot(df[MODERATOR_KEY])
        plt.title(f'Moderator Score for {df.shape[0]} comments ({csv_name})')
        plt.savefig(f'{path}/moderator_score_dist.png')

        # Value counts of the moderator score column and save the plot
        plt.figure(figsize=(15, 5))
        df[BEHAV_TYPE].value_counts().plot(kind='barh', rot=45)
        print(df[BEHAV_TYPE].value_counts())
        plt.title(f'All Behav Type Dist for {df.shape[0]} comments ({csv_name})')
        plt.savefig(f'{path}/behav_type_dist.png')

    print(f'Comparison scores for {csv_name} with {df.shape[0]} comments')
    print('-'*100)

    # Requires class predictions, not floating point values
    # print(f"Cohen's Kappa Score = {cohen_kappa_score(df[MODERATOR_KEY], df[PERSPECTIVE_KEY])}")

    print(f"Pearson's Correlation = {pearsonr(df[MODERATOR_KEY], df[PERSPECTIVE_KEY])}")
    print(f"Spearman's Correlation = {spearmanr(df[MODERATOR_KEY], df[PERSPECTIVE_KEY])}")
    print(f"Kendall's Correlation = {kendalltau(df[MODERATOR_KEY], df[PERSPECTIVE_KEY])}")
    print('-'*100, '\n')

def norm_vio():
    removed_comments = pd.read_csv('norm-vio/reddit-removal-log.csv')
    print(removed_comments.shape, removed_comments.columns)

    logger = setup_logger(f'analysis_log', f'analysis_log.log')
    config_fn = os.environ.get("CONF_FP", "/isi_darma/isi_darma/darma_online/src/experiments/analysis_config.yaml")
    config = load_config(logger, config_fn=config_fn)
    mod_classifier = PerspectiveAPIModerator(logger, config)

    # Run each comment through mod_classifier
    tick = time.time()
    for count, comment in enumerate(removed_comments['body'][1937:]):
        if count % 50 == 0:
            print(f'Processed {count} comments in {time.time() - tick} seconds')
            time.sleep(60)
            tick = time.time()

        _, _, _ = mod_classifier.measure_toxicity(comment)


if __name__ == '__main__':

    # for c in ['mod_agree', 'intersection_scores']:
    #     run(c, plot=True)

    norm_vio()
