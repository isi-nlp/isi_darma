# author: Justin Cho 

from mturk_analysis import filter_users, create_bot_mean_plots, ITERATION_DATES, get_annotated_datafiles_for_dates, extract_data_of_interest, SURVEY_QUESTIONS, t_test
from loguru import logger 
import pandas as pd 
import numpy as np 
from scipy import stats
from collections import defaultdict, Counter
from argparse import ArgumentParser
import operator

OPS = {'>': operator.gt, '<': operator.lt, '=': operator.eq, '>=': operator.ge, '<=': operator.le, '!=': operator.ne}

parser = ArgumentParser()
parser.add_argument("-idx", "--iteration_idx", type=int, default=7, help="iteration idx for the survey data")
parser.add_argument("-n", "--normalize", action="store_true", help="normalize the scores")
parser.add_argument("-c", "--combine", action="store_true", help="combine first person pov and thid person pov data")
parser.add_argument(
        "--partition_by", "-p", type=str, help="partition the data by which variable", default=None,
    )
parser.add_argument(
    "--partition_threshold", "-t", type=int, help="partition threshold"
)
parser.add_argument(
    "--partition_operator", "-o", type=str, help="partition operator", choices=['=', '<', '>', '>=', '<=']
)
args = parser.parse_args()


eval_categories = sorted(list(set(SURVEY_QUESTIONS.values())))

if args.iteration_idx == 4:
    eval_categories = ["coherency", "engaging", "understanding", "convincing"]
else: 
    eval_categories = ["specific", "fair", "engaging", "respectful"]

# load iteration 3 data 
first_person_pov_dates = ITERATION_DATES[args.iteration_idx-1]
first_person_pov_data_files = get_annotated_datafiles_for_dates(first_person_pov_dates)

first_person_pov_mturk_results = []
for fn in first_person_pov_data_files:
    try:
        mturk_result = extract_data_of_interest(fn)
        if mturk_result:
            first_person_pov_mturk_results += mturk_result
    except Exception as e:
        logger.exception(e)
        print(e)
        print(fn)
        

# load iteration survey data
third_person_pov_dates = ITERATION_DATES[args.iteration_idx]
SURVEY_DATA_PATH="/home/darma/work/boteval.prod/darma-task/survey-data-prod/data/"
third_person_pov_data_files = get_annotated_datafiles_for_dates(third_person_pov_dates, base_data_dir=SURVEY_DATA_PATH)

third_person_pov_mturk_results = []
for fn in third_person_pov_data_files:
    try:
        mturk_result = extract_data_of_interest(fn)
        if mturk_result:
            third_person_pov_mturk_results += mturk_result
    except Exception as e:
        logger.exception(e)
        print(e)
        print(fn)

third_person_pov_res2bot_type = {} 
for first_person_pov_res in first_person_pov_mturk_results:
    key = f"{first_person_pov_res['topic_id']}-{first_person_pov_res['thread_id']}"
    third_person_pov_res2bot_type[key] = first_person_pov_res["bot_type"]

for third_person_pov_res in third_person_pov_mturk_results: 
    # get bot type from first person pov results 
    third_person_pov_res["bot_type"] = third_person_pov_res2bot_type[third_person_pov_res['topic_id']]

first_df = pd.DataFrame(first_person_pov_mturk_results)
third_df = pd.DataFrame(third_person_pov_mturk_results)

if args.combine:
# combine iteration 3 and iteration 4 data 
    df = pd.concat([first_df, third_df])
else: 
    df = pd.DataFrame(third_person_pov_mturk_results)



# repeat analysis in mturk_analysis.py
df = filter_users(df)

# partition
if args.partition_by is not None:
    df = df[OPS[args.partition_operator](df[args.partition_by], args.partition_threshold)]

users = df.groupby("worker_id").agg("count")
print(users['topic_id'])

if not args.combine: 
    sig_diff = t_test(df, iteration_idx=args.iteration_idx, normalize=args.normalize)
    create_bot_mean_plots(df.copy(), iteration_idx=args.iteration_idx, normalize=args.normalize, sig_diff=sig_diff, partition_by=args.partition_by, partition_threshold=args.partition_threshold, partition_operator=args.partition_operator)
else: 
    assert False
    create_bot_mean_plots(df.copy(), iteration_idx=args.iteration_idx, normalize=args.normalize, name="first_third_combined", partition_by=args.partition_by, partition_threshold=args.partition_threshold, partition_operator=args.partition_operator)

# check for inconsistency in the same user's ratings
combined_df = pd.concat([first_df, third_df])
# combined_df.loc[:, 'topic_id'] = combined_df.apply(lambda row: f"{row['topic_id']}-{row['thread_id']}" if '-' not in row['topic_id'] else row['topic_id'], axis=1)

# create a new column that is just topic_id split with - 
combined_df.loc[:, 'super_topic_id'] = combined_df.apply(lambda row: row['topic_id'].split('-')[0], axis=1)
duplicated_rows = combined_df[combined_df.duplicated(subset=['topic_id', 'worker_id'], keep=False)].sort_values(by=['topic_id', 'worker_id'])

print(len(duplicated_rows)//2)
cat_diffs = defaultdict(list) 
inconsistency_df_data =[] 
for idx in range(0, len(duplicated_rows)-1,2): 
    # calculate difference between two rows for eval_catgories 
    row_data ={} 
    for cat in eval_categories: 
        cat_diffs[cat].append(abs(duplicated_rows.iloc[idx][cat] - duplicated_rows.iloc[idx+1][cat]))
        row_data[cat] = abs(duplicated_rows.iloc[idx][cat] - duplicated_rows.iloc[idx+1][cat])
        row_data['worker_id'] = duplicated_rows.iloc[idx]['worker_id']
        row_data["topic_id"] = duplicated_rows.iloc[idx]['topic_id']
    inconsistency_df_data.append(row_data)

for k,v in cat_diffs.items(): 
    print(f"{k}: {np.mean(v):.2f} +/- {np.std(v):.2f}, max: {np.max(v):.2f}, min: {np.min(v):.2f}")
    print(Counter(v))

if inconsistency_df_data: 
    inconsistency_df = pd.DataFrame(inconsistency_df_data)
    per_worker_mean = inconsistency_df.groupby("worker_id").agg(["mean", "max", "count"])

    print(per_worker_mean)
    
# examine variance within same super_topic_id 
# for super_topic_id in set(df.super_topic_id.tolist()):
#     create_bot_mean_plots(df[df['super_topic_id'] == super_topic_id], iteration_idx=4, normalize=False, title=f"topic_id={super_topic_id}")
#     create_bot_mean_plots(df[df['super_topic_id'] == super_topic_id], iteration_idx=4, normalize=True, title=f"topic_id={super_topic_id}")

# A1E77HZO63E334      9
# A1ELPYAFO7MANS     37
# A1HKYY6XI2OHO1     24
# A2FP41BSPG0Y4A     11
# A2GO2OXS4VM1PR    101
# A2T11H7YI7QPGD    105
# A2Y7FD1D7PUGBL      6
# A3EU8ENRH654SB     62
# A9HQ3E0F2AGVO      94
# for worker_id in ["A9HQ3E0F2AGVO", "A2T11H7YI7QPGD", "A2GO2OXS4VM1PR"]: 
#     create_bot_mean_plots(df[df['worker_id'] == worker_id], iteration_idx=4, normalize=False, title=f"worker_id={worker_id}")
#     create_bot_mean_plots(df[df['worker_id'] == worker_id], iteration_idx=4, normalize=True, title=f"worker_id={worker_id}")