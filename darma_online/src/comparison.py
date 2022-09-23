import time
from typing import List
import numpy as np
from tqdm import tqdm
import pandas as pd

from darma_online.pipeline.moderation_classifiers import PerspectiveAPIModerator
from darma_online.logging_setup import setup_logger


def get_perspective_scores():
    df = read_comments()
    df['Model Decision'] = df['model_score'].apply(to_binary)
    tick = time.time()
    df['Perspec Decision'], df['Perspec Score'], df['Perspec - Behav Type'] = call_perspective(df['body'])
    print(df.head(10))
    df.to_csv('data/output_scores_compared.csv')
    print(f'DONE in {time.time() - tick} seconds!!')

def call_perspective(comments: List[str]):
    logger = setup_logger('comparison', 'logs/comparison.log', test=False)
    perspective = PerspectiveAPIModerator(logger)
    decision, score, behav_type = np.array([]), np.array([]), np.array([])
    for idx, comm in tqdm(enumerate(comments), desc='Calling Perspective API', total=len(comments), unit='comments'):
        logger.info(f'Check score for comment #{idx} - {comm}')
        d, s, t = perspective.measure_toxicity(comm)
        decision, score, behav_type = np.append(decision, d), np.append(score, s), np.append(behav_type, t)
    return decision, score, behav_type

def read_comments():
    # df = pd.read_csv('data/output_scores.csv', verbose=True, skiprows=range(10, 155965), index_col=0)
    df = pd.read_csv('data/output_scores.csv', verbose=True, index_col=0)
    return df

def to_binary(x):
    return 1 if x >= 0.5 else 0

if __name__ == '__main__':
    get_perspective_scores()

    # <09/23/2022 02:35:08 PM> [ERROR] <58> <measure_toxicity> Exception occurred:
    # <HttpError 429 when requesting https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=AIzaSyC30WbnABE2zjzK4Be58ytkatxgOC3yg9I&
    # alt=json returned "Quota exceeded for quota metric 'Analysis requests (AnalyzeComment)' and limit 'Analysis requests (AnalyzeComment) per minute' of service '" \
    #                   "commentanalyzer.googleapis.com' for consumer 'project_number:416769962659'.".
    # Details: "[{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', " \
    #          "'reason': 'RATE_LIMIT_EXCEEDED', 'domain': 'googleapis.com', " \
    #          "'metadata': {'quota_location': 'global', 'quota_metric': 'CommentAnalyzerService/analyze_requests', " \
    #          "'quota_limit_value': '60', 'consumer': 'projects/416769962659', 'quota_limit': 'AnalyzeRequestsPerMinutePerProject', " \
    #          "'service': 'commentanalyzer.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.Help', " \
    #          "'links': [{'description': 'Request a higher quota limit.', 'url': 'https://cloud.google.com/docs/quota#requesting_higher_quota'}]}]">
    # for comment: i can give you the rowlet. Setting toxicity to 0 with empty behaviour type.

