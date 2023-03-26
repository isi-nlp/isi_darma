import time
from glob import glob
from os.path import join
from typing import List
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import classification_report, ConfusionMatrixDisplay

from darma_online.pipeline.moderation_classifiers import PerspectiveAPIModerator
from darma_online.logging_setup import setup_logger

data_dir = '/isi_darma/isi_darma/darma_online/src/darma_online/data'

def get_perspective_scores():
    logger = setup_logger('comparison', 'logs/comparison.log', test=False)
    df = read_comments()
    df['Model Decision'] = df['model_score'].apply(to_binary)
    splits = range(0, len(df), 1000)

    for idx, split in enumerate(splits):
        tick = time.time()
        df_split = df.iloc[split:split+1000]
        df_split['Perspec Decision'], df_split['Perspec Score'], df_split['Perspec - Behav Type'] = call_perspective(df_split['body'], logger)
        df_split.to_csv(f'{data_dir}/output_scores_compared_{idx}.csv')
        logger.info(f'Split {idx+1} DONE in {time.time() - tick} seconds!!')

def call_perspective(comments: List[str], logger):
    perspective = PerspectiveAPIModerator(logger)
    decision, score, behav_type = np.array([]), np.array([]), np.array([])
    for idx, comm in enumerate(comments):
        logger.info(f'Check score for comment #{idx} - {comm}')
        d, s, t = perspective.measure_toxicity(comm)
        decision, score, behav_type = np.append(decision, d), np.append(score, s), np.append(behav_type, t)
    return decision, score, behav_type

def read_comments():
    # df = pd.read_csv('data/output_scores.csv', verbose=True, skiprows=range(10, 155965), index_col=0)
    df = pd.read_csv(f'{data_dir}/output_scores.csv', verbose=True, index_col=0)
    return df

def to_binary(x):
    return 1 if x >= 0.5 else 0

def calculate_results():
    local_data_dir = '/Users/darpanjain/Data/USC/RA - ISI/isi_darma/darma_online/src/darma_online/data'

    # Combine results
    # csv_files = glob(join(f'{local_data_dir}/comparison_scores/comp_scores_all', '*.csv'))
    # df = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)
    # print(df.info())
    # df.to_csv(f'{local_data_dir}/comparison_scores/combined_scores_all.csv')

    df = pd.read_csv(f'{local_data_dir}/comparison_scores/combined_scores_11k.csv', index_col=0)
    # df = pd.read_csv(f'{local_data_dir}/comparison_scores/combined_scores_all.csv', index_col=0)
    print(df.info())

    df['Intersection'] = [1 if (df['Model Decision'][idx] == 1 == df['Perspec Decision'][idx]) else 0 for idx in range(len(df))]
    print(f'Intersection: {len(df["Intersection"])}, {len(df["Model Decision"])}')

    # Moderator Results
    moderator = classification_report(df['moderated'], df['Model Decision'], target_names=['Unmoderated', 'Moderated'])
    # ConfusionMatrixDisplay.from_predictions(df['moderated'], df['Model Decision'], display_labels=['Unmoderated', 'Moderated'], normalize='true')
    # plt.title('Moderator Results')
    print(f'moderator: \n {moderator}')
    # plt.show()

    # Perspective Results
    perspective = classification_report(df['moderated'], df['Perspec Decision'], target_names=['Unmoderated', 'Moderated'])
    # ConfusionMatrixDisplay.from_predictions(df['moderated'], df['Perspec Decision'], display_labels=['Unmoderated', 'Moderated'], normalize='true')
    # plt.title('Perspective Results')
    print(f'perspective: \n {perspective}')
    # plt.show()

    # Intersection Results
    inter_results = classification_report(df['moderated'], df['Intersection'], target_names=['Unmoderated', 'Moderated'])
    # ConfusionMatrixDisplay.from_predictions(df['moderated'], df['Intersection'], display_labels=['Unmoderated', 'Moderated'], normalize='true')
    # plt.title('Intersection Results')
    print(f'intersection: \n {inter_results}')
    # plt.show()


if __name__ == '__main__':
    calculate_results()
    # get_perspective_scores()
