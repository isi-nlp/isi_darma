# author: Justin Cho 

from mturk_analysis import filter_users, create_bot_mean_plots, ITERATION_DATES, get_annotated_datafiles_for_dates, extract_data_of_interest, SURVEY_QUESTIONS
from loguru import logger 
import pandas as pd 
import numpy as np 
from scipy import stats
from collections import defaultdict, Counter

eval_categories = sorted(list(set(SURVEY_QUESTIONS.values())))

# load iteration 3 data 
it3_dates = ITERATION_DATES[3]
it3_data_files = get_annotated_datafiles_for_dates(it3_dates)

it3_mturk_results = []
for fn in it3_data_files:
    try:
        mturk_result = extract_data_of_interest(fn)
        if mturk_result:
            it3_mturk_results += mturk_result
    except Exception as e:
        logger.exception(e)
        print(e)
        print(fn)
        

# load iteration 4 survey data
it4_dates = ITERATION_DATES[4]
SURVEY_DATA_PATH="/home/darma/work/boteval.prod/darma-task/survey-data-prod/data/"
it4_data_files = get_annotated_datafiles_for_dates(it4_dates, base_data_dir=SURVEY_DATA_PATH)

it4_mturk_results = []
for fn in it4_data_files:
    try:
        mturk_result = extract_data_of_interest(fn)
        if mturk_result:
            it4_mturk_results += mturk_result
    except Exception as e:
        logger.exception(e)
        print(e)
        print(fn)

it4_res2bot_type = {} 
for it3_res in it3_mturk_results:
    key = f"{it3_res['topic_id']}-{it3_res['thread_id']}"
    it4_res2bot_type[key] = it3_res["bot_type"]

for it4_res in it4_mturk_results: 
    # get bot type from it3 results 
    it4_res["bot_type"] = it4_res2bot_type[it4_res['topic_id']]


# it4_mturk_results = it3_mturk_results.copy() + it3_mturk_results.copy() + it3_mturk_results.copy()
        
# combine iteration 3 and iteration 4 data 
it3_df = pd.DataFrame(it3_mturk_results)
it4_df = pd.DataFrame(it4_mturk_results)
combined_df = pd.concat([it3_df, it4_df])



# repeat analysis in mturk_analysis.py
df = filter_users(combined_df)
# df = filter_users(it4_df)

users = df.groupby("worker_id").agg("count")
print(users['topic_id'])

# df = df[(np.abs(stats.zscore(df[eval_categories])) < 4).all(axis=1)]
create_bot_mean_plots(df, iteration_idx=4, normalize=False)
create_bot_mean_plots(df.copy(), iteration_idx=4, normalize=True)
create_bot_mean_plots(it3_df.copy(), iteration_idx=3, normalize=True)
# create_bot_mean_plots(it4_df.copy(), iteration_idx=4, normalize=True)

# check for inconsistency in the same user

df.loc[:, 'topic_id'] = df.apply(lambda row: f"{row['topic_id']}-{row['thread_id']}" if '-' not in row['topic_id'] else row['topic_id'], axis=1)

duplicated_rows = df[df.duplicated(subset=['topic_id', 'worker_id'], keep=False)].sort_values(by=['topic_id', 'worker_id'])

print(len(duplicated_rows))
cat_diffs = defaultdict(list) 
inconsistency_df_data =[] 
for idx in range(len(duplicated_rows)-1): 
    # calculate difference between two rows for eval_catgories 
    row_data ={} 
    for cat in eval_categories: 
        cat_diffs[cat].append(abs(duplicated_rows.iloc[idx][cat] - duplicated_rows.iloc[idx+1][cat]))
        row_data[cat] = abs(duplicated_rows.iloc[idx][cat] - duplicated_rows.iloc[idx+1][cat])
        row_data['worker_id'] = duplicated_rows.iloc[idx]['worker_id']
        row_data["topic_id"] = duplicated_rows.iloc[idx]['topic_id']

for k,v in cat_diffs.items(): 
    print(f"{k}: {np.mean(v):.2f} +/- {np.std(v):.2f}, max: {np.max(v):.2f}, min: {np.min(v):.2f}")
    print(Counter(v))
    
    
# examine variance within same topic_id 
