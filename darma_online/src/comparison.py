import time
from typing import List
import numpy as np
import pandas as pd

from darma_online.pipeline.moderation_classifiers import PerspectiveAPIModerator
from darma_online.logging_setup import setup_logger


def get_perspective_scores():
    data_dir = '/isi_darma/isi_darma/darma_online/src/darma_online/data'
    logger = setup_logger('comparison', 'logs/comparison.log', test=False)

    df = read_comments(data_dir)
    df['Model Decision'] = df['model_score'].apply(to_binary)
    splits = range(0, len(df), 1000)

    for idx, split in enumerate(splits):
        tick = time.time()
        df_split = df.iloc[split:split+1000]
        df_split['Perspec Decision'], df_split['Perspec Score'], df_split['Perspec - Behav Type'] = call_perspective(df_split['body'], logger)
        df.to_csv(f'{data_dir}/output_scores_compared_{idx}.csv')
        logger.info(f'Split {idx+1} DONE in {time.time() - tick} seconds!!')

def call_perspective(comments: List[str], logger):
    perspective = PerspectiveAPIModerator(logger)
    decision, score, behav_type = np.array([]), np.array([]), np.array([])
    for idx, comm in enumerate(comments):
        logger.info(f'Check score for comment #{idx} - {comm}')
        d, s, t = perspective.measure_toxicity(comm)
        decision, score, behav_type = np.append(decision, d), np.append(score, s), np.append(behav_type, t)
    return decision, score, behav_type

def read_comments(data_dir):
    # df = pd.read_csv('data/output_scores.csv', verbose=True, skiprows=range(10, 155965), index_col=0)
    df = pd.read_csv(f'{data_dir}/output_scores.csv', verbose=True, index_col=0)
    return df

def to_binary(x):
    return 1 if x >= 0.5 else 0

if __name__ == '__main__':
    get_perspective_scores()
