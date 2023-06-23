# author: Justin Cho
# usage: python mturk_analysis.py -idx <iteration idx>
# e.g. python mturk_analysis.py -idx 1
# add iteration dates and adjust BASE_DATA_DIR as necessary for new iterations

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})
from matplotlib.patches import Patch
import seaborn as sns

import numpy as np
import scipy.stats as st
from tabulate import tabulate
from loguru import logger
from argparse import ArgumentParser
import operator
from collections import defaultdict
import scipy.stats as stats
from sklearn.utils import resample

OPS = {'>': operator.gt, '<': operator.lt, '=': operator.eq, '>=': operator.ge, '<=': operator.le, '!=': operator.ne}

BASE_DATA_DIR = "/home/darma/work/boteval.prod/darma-task/data-prod/data/"
# BASE_DATA_DIR = "/home/darma/work/boteval.prod/darma-task/data/data/" # sandbox

SURVEY_QUESTIONS = {
    "how coherent was the conversation?": "coherency",
    "how likely are you to continue chatting with the moderator?": "engaging",
    "to what degree did the moderator understand your point of view?": "understanding",
    "to what degree did the moderator convince you to change your behavior?": "convincing",
    "if you were the user, how likely are you to continue chatting with the moderator?": "engaging", 
    "how successful was the moderator in convincing to change the user's behavior?": "convincing",
    "how well did it seem like the moderator understand the user's point of view?": "understanding",
    "how coherent was the conversation?": "coherency",
    'did the moderator make specific suggestions for the given conversation to facilitate cooperation?': "specific",
    'was the moderator impartial?': "fair", 
    'was the moderator fair to all users involved in the conversation?': "fair", 
    'did you (the user) become more engaged and willing to cooperate? (e.g. provide more details or ask sincere questions to make the conversation more constructive or be more persuasive)': "engaging", 
    'did the moderated user become more engaged and willing to cooperate? (e.g. provide more details or ask sincere questions to make the conversation more constructive or be more persuasive)': "engaging",
    'did the moderated user become more respectful and less abusive? (e.g. less profanity, unconstructive criticism, or condescending sarcasm)': "respectful",
    'did you (the user) become more respectful and less abusive? (e.g. less profanity, unconstructive criticism, or condescending sarcasm)': "respectful",
    'how much did you agree with the arguments/viewpoints of the user that you were acting as?': 'agreement',
    'how much did you agree with the arguments/viewpoints of the moderated user?': 'agreement',
    'how much did you like the person that you were acting as?': 'likeability',
    'how much did you like the moderated user?': 'likeability',
    'how could the moderator have been more effective? (e.g. reduce repetition, less generic suggestions, more examples, etc.)': 'moderator_feedback',
    '(optional) how could the moderator have been more effective? (e.g. reduce repetition, less generic suggestions, more examples, etc.)': 'moderator_feedback',
    'how can we improve the task design or survey questions?': 'task_feedback',
    '(optional) how can we improve the task design or survey questions?': 'task_feedback'
}

ITERATION1_MOD_CHATS = [55, 784, 1014, 1068, 332, 410, 476, 51, 68, 132]
ITERATION1_NVC_chats = [1444, 1322, 1141, 570, 126, 858, 785, 696, 572, 444]
ITERATION_DATES = {
    1: [20230107, 20230108, 20230109],
    2: [20230201, 20230202, 20230203, 20230204, 20230205, 20230206, 20230207, 20230208],
    3: [20230413, 20230414, 20230415, 20230416, 20230417],
    4: [20230423, 20230424],
    5: [20230502, 20230503, 20230504, 20230505, 20230506, 20230507, 20230516], 
    6: [20230609, 20230610, 20230611, 20230612, 20230613, 20230614, 20230615, 20230616, 20230617],
    7: [20230617, 20230618, 20230619]
}

PLOT_WIDTH=12
PLOT_HEIGHT=8
MIN_TASK_COUNT = 5

HATCHES = ['/', '\\', '-', 'x', '+', '//', '\\\\']


def extract_bot_type(endpoint: str) -> str:
    persona_configs = json.load(
        open("/home/darma/work/boteval.prod/darma-task/persona_configs.json")
    )
    persona_names = [c["id"] for c in persona_configs]

    for name in persona_names:
        if name in endpoint:
            return name
    return None

def filter_users(df): 
    # drop users if they have less than MIN_TASK_COUNT tasks
    counts_per_worker = df.groupby("worker_id").agg("count")["engaging"]
    workers_to_drop = counts_per_worker[counts_per_worker < MIN_TASK_COUNT].index.tolist()
    df = df[~df["worker_id"].isin(workers_to_drop)]
    return df 

def normalize_scores_by_user(df, metrics_to_normalize:List[str]):     
    
    # get mean & std per dimension per worker id 
    stats_per_worker = df[metrics_to_normalize + ['worker_id']].groupby("worker_id").agg(["mean", "std"])
    # stats_per_worker = df[metrics_to_normalize + ['worker_id']].groupby("worker_id").agg(["mean", ""])
    
    # adjust scores based on the mean and std 
    for idx, row in df.iterrows(): 
        worker_id = row["worker_id"]
        for metric in metrics_to_normalize: 
            stats = stats_per_worker.loc[worker_id][metric]
            df.at[idx, metric] = st.norm.cdf((row[metric] - stats['mean']) / (stats['std']+1e-6))
            # df.at[idx, metric] = (row[metric] - stats['mean']) / (stats['std']+1e-6)
            # df.at[idx, metric] = 1 
    
    return df 

def get_annotated_datafiles_for_dates(dates: List[str], base_data_dir:str=BASE_DATA_DIR) -> List[str]:
    data_folders = [p for p in Path(base_data_dir).glob("*") if int(p.name) in dates]
    data_files = []
    for folder in data_folders:
        fns = folder.glob("*.json")
        data_files.extend(fns)

    logger.info(f"# of data files found: {len(data_files)}")
    return data_files


def extract_data_of_interest(mturk_fn: str, iteration_idx=None, is_survey=False) -> List[Dict[str, Any]]:
    """extract only the data that is relevant for analysis

    Args:
        mturk_fn (str): filepath

    Returns:
        Dict[str,Any]: dictionary of relevant results
    """

    with open(mturk_fn) as f:
        data = json.load(f)

    # chat number
    chat_num = mturk_fn.name.split("chat")[-1].split("_")[0]
    
    # get conversation
    messages = data["messages"]
    
    # extract speaker order
    speaker_order = []
    for m in messages: 
        if m["user_id"] == "context":
            continue 
        elif m["user_id"] not in speaker_order: 
            speaker_order.append(m["user_id"])

    thread_id = messages[0]["thread_id"]

    # ignore sandbox results for analysis (in case any got mixed in here)
    if "mturk_sandbox" in data["data"]:
        return None

    # getting bot type (legacy code for older iterations that didn't store this information)
    if iteration_idx == 1:
        bot_type = "moderator" if int(chat_num) in ITERATION1_MOD_CHATS else "wisebeing"
        if bot_type == "wisebeing":
            assert int(chat_num) in ITERATION1_NVC_chats, chat_num
    elif iteration_idx == 2:
        # hacky way to do it for second iteration 
        bot_type = extract_bot_type(data["users"][0]["data"]["next"])
    else: 
        bot_type = data["meta"]["persona_id"]

    data_of_interest = [] 
    # get ratings
    ratings = data["data"]["ratings"]
        
    def format_results(user_ratings): 
        
        filtered_ratings = {
            SURVEY_QUESTIONS[k.lower().strip()]: int(v)
            for k, v in user_ratings.items()
            if SURVEY_QUESTIONS[k.lower().strip()] not in [
                "moderator_feedback",
                "task_feedback"
            ]
        }
        
        # if len(filtered_ratings) != 4: 
        #     import pdb; pdb.set_trace() 
        
        order = speaker_order.index(user_id) if user_id in speaker_order else -1
        
        formatted_ratings = {
            "topic_id": chat_num,
            "bot_type": bot_type,
            "worker_id": user_id,
            "messages": messages,
            "speaker_order": order, 
            "thread_id": thread_id,
            **filtered_ratings, 
        }
        formatted_ratings["human_words"], formatted_ratings["bot_words"] = get_human_bot_number_words(messages)
        
        return formatted_ratings
            
    if isinstance(list(ratings.values())[0], dict): 
        for user_id, user_ratings in ratings.items(): 
            data_of_interest.append(format_results(user_ratings))
    else: 
        # legacy code for older iterations that didn't store multi-user info
        data_of_interest.append(format_results(ratings))

    return data_of_interest


def get_human_bot_number_words(messages):
    human = 0
    bot = 0
    for msg in messages:
        if msg["user_id"] == "context":
            continue
        if msg["user_id"] == "bot01" or msg["user_id"] == "Moderator":
        # if msg["user_id"] == "bot01": 
            bot += len(msg["text"].split())
        else:
            human += len(msg["text"].split())

    return human, bot


def create_word_count_plots(df:pd.DataFrame, iteration_idx:int=None, normalize:bool=False, sig_diff=None): 
    if normalize: 
        if iteration_idx < 5: 
            metrics_to_normalize = ["coherency", "engaging", "understanding", "convincing", "human_words", "bot_words"]
        else: 
            metrics_to_normalize = ["specific", "fair", "engaging", "respectful", "agreement", "likeability", "human_words", "bot_words"]
        df = normalize_scores_by_user(df, metrics_to_normalize)

    categories_of_interest = ["human_words", "bot_words"]
    cols_to_drop = ["topic_id", "worker_id", "messages"] 
    df = df.drop(cols_to_drop, axis=1)
    # df = df[~df['bot_type'].isin(['witty'])]

    agg_by_bots = df.groupby("bot_type").agg(["mean", "median", "sem", "count"])[
        categories_of_interest
    ]
    
    agg_by_bots.to_csv(f"it{iteration_idx}_{normalize=}_word_count_results.csv")
    
    agg_by_bots = agg_by_bots.rename(index={"moderator": "GPT-Moderator", "wisebeing": "GPT-NVC", "witty": "GPT-Witty", "stern": "GPT-Stern", "moderator-cosmo-xl": "Cosmo-XL", "moderator-prosocial": "Canary+Cosmo-XL", "socratic": "GPT-Socratic"})
    
    
    bot_order = ["Cosmo-XL", "Canary+Cosmo-XL", "GPT-Moderator", "GPT-Stern", "GPT-Witty", "GPT-NVC", "GPT-Socratic"]
    # reorder the bot_types with bot_order
    agg_by_bots = agg_by_bots.reindex(bot_order)
    
    print(
        df.groupby("bot_type").agg(["mean", "count"])[categories_of_interest]
    )
    
    means_by_bot_type = {}
    for row in agg_by_bots.iterrows():
        means_by_bot_type[row[0]] = [round(row[1][l]["mean"], 2) for l in categories_of_interest]

    x = np.arange(len(categories_of_interest))  # the label locations

    fig, ax = plt.subplots()
    number_of_bots = len(means_by_bot_type)
    width = 1 / number_of_bots * 1.7
    start_width = x - width * number_of_bots / 4

    max_bar = 0

    for idx, (bot_type, means) in enumerate(means_by_bot_type.items()):
        max_bar = max(max_bar, max(means))

        bot_count = int(agg_by_bots.loc[bot_type][categories_of_interest[0]]['count'])
        palette_rocket = sns.color_palette("rocket_r", number_of_bots)
        palette_mako = sns.color_palette("mako_r", 2)
        if "gpt" in bot_type.lower():
            color = palette_rocket[idx-2]
        else:
            color = palette_mako[idx]

        rects1 = ax.bar(start_width, means, width / 2, label=f"{bot_type} [{bot_count}]", color=color, hatch=HATCHES[idx])
        
        stds = [agg_by_bots.loc[bot_type][cat]['sem'] for cat in categories_of_interest]
        ax.errorbar(start_width, means, stds, markeredgecolor="black", ecolor="black", fmt='.', c='white')
        
        start_width += width / 2
        ax.bar_label(rects1, padding=15, rotation=45)

    # Add some text for labels, title and custom x-axis tick labels, etc.
    plt.title("Word Count Results")
    
    if normalize: 
        ax.set_ylabel(f"Normalized word count")
    else: 
        ax.set_ylabel("Word count")
    
    # ax.set_ylim([0, 540])
    # if normalize:
    #     ax.set_ylim([0, 1.1])
    # else:
    #     ax.set_ylim([0, 540])
    ax.set_ylim([0, max_bar * 1.2])
    ax.set_xticks(x, categories_of_interest)
    leg = ax.legend()

    leg.get_frame().set_alpha(0)

    fig.tight_layout()
    fig.set_size_inches(PLOT_WIDTH, PLOT_HEIGHT)
    fig.savefig(f"it{iteration_idx}_{normalize=}_words_mean_results.png", dpi=100)

def create_bot_mean_plots(df: pd.DataFrame , iteration_idx:int=None, normalize:bool=False, sig_diff=None, custom_name:str="", title:str="", partition_by="", partition_threshold=None, partition_operator=""): 
    """creates a bar plot of the mean scores for each bot type 
    
    input:
        df:pd.DataFrame: dataframe of survey results
        iteration_idx:int: iteration number
        normalize:bool: whether to normalize the scores by user
        title:str: title of the plot
    
    returns: None 
    """
    if normalize:
        if iteration_idx < 5: 
            metrics_to_normalize = ["coherency", "engaging", "understanding", "convincing", "human_words", "bot_words"]
        else: 
            metrics_to_normalize = ["specific", "fair", "engaging", "respectful", "agreement", "likeability", "human_words", "bot_words"]
        df = normalize_scores_by_user(df, metrics_to_normalize)
    
    eval_categories = sorted(list(set(SURVEY_QUESTIONS.values())))
    if iteration_idx < 5: 
        eval_categories = ["coherency", "engaging", "understanding", "convincing"]
    if iteration_idx >= 5: 
        eval_categories = ["specific", "fair", "engaging", "respectful"]


    num_unique_workers = len(df.groupby("worker_id").agg(["count"]))
    logger.info(f"Number of unique workers in this iteration: {num_unique_workers}")

    cols_to_drop = ["topic_id", "worker_id", "messages"] 
    df = df.drop(cols_to_drop, axis=1)
    # df = df[~df['bot_type'].isin(['witty'])]

    print(
        df.groupby("bot_type").agg(["mean", "sem", "count"])[eval_categories]
    )

    agg_by_bots = df.groupby("bot_type")[eval_categories].agg(["mean", "median", "sem", "count"])[eval_categories]
    
    agg_by_bots = agg_by_bots.rename(index={"moderator": "GPT-Moderator", "wisebeing": "GPT-NVC", "witty": "GPT-Witty", "stern": "GPT-Stern", "moderator-cosmo-xl": "Cosmo-XL", "moderator-prosocial": "Canary+Cosmo-XL", "socratic": "GPT-Socratic"})
    
    
    bot_order = ["Cosmo-XL", "Canary+Cosmo-XL", "GPT-Moderator", "GPT-Stern", "GPT-Witty", "GPT-NVC", "GPT-Socratic"]
    # reorder the bot_types with bot_order
    agg_by_bots = agg_by_bots.reindex(bot_order)
    
    if not custom_name: 
        agg_by_bots.to_csv(f"it{iteration_idx}_{normalize=}_bot_mean_results.csv")
    else: 
        agg_by_bots.to_csv(f"it{iteration_idx}_{normalize=}_{name=}_bot_mean_results.csv")
    
    means_by_bot_type = {}
    for row in agg_by_bots.iterrows():
        means_by_bot_type[row[0]] = [round(row[1][l]["mean"], 2) for l in eval_categories]
    
    x = np.arange(len(eval_categories))  # the label locations
    fig, ax = plt.subplots()
    number_of_bots = len(means_by_bot_type)
    width = 1 / number_of_bots * 1.7
    start_width = x - width * number_of_bots / 4

    max_bar = 0
    max_err = 0
    
    for idx, (bot_type, means) in enumerate(means_by_bot_type.items()):
        max_bar = max(max_bar, max(means))

        bot_count = int(agg_by_bots.loc[bot_type][eval_categories[0]]['count'])
        palette_rocket = sns.color_palette("rocket_r", number_of_bots)
        palette_mako = sns.color_palette("mako_r", 2)
        if "gpt" in bot_type.lower():
            color = palette_rocket[idx-2]
        else:
            color = palette_mako[idx]
        
        stds = [agg_by_bots.loc[bot_type][cat]['sem'] for cat in eval_categories]
        max_err = max(max_err, max(stds))
        
        for j in range(4):
            if j == 0:
                rects1 = ax.bar(start_width[j], means[j], width / 2, label=f"{bot_type} [{bot_count}]", color=color, hatch=HATCHES[idx])
            else:
                rects1 = ax.bar(start_width[j], means[j], width / 2, label=None, color=color, hatch=HATCHES[idx])
            ax.errorbar(start_width[j], means[j], stds[j], markeredgecolor="black", ecolor="black", fmt='.', c='white')
            category = eval_categories[j]
            weight = 'light'
            if bot_type in sig_diff[category]:
                weight = 'bold'
            # if iteration_idx == 6:
            #     pad = 25
            # elif iteration_idx == 7:
            #     pad = 20
            ax.bar_label(rects1, padding=stds[j]*50+20, rotation=90, weight=weight)
            

        start_width += width / 2

    handles, labels = ax.get_legend_handles_labels()
    leg1 = plt.legend(handles[:2], labels[:2], loc=(0.12, 0.87))
    leg1.get_frame().set_alpha(0)
    ax.add_artist(leg1)
    leg2 = plt.legend(handles[2:], labels[2:], loc=(0.54, 0.72))
    leg2.get_frame().set_alpha(0)
    ax.add_artist(leg2)

    # Add some text for labels, title and custom x-axis tick labels, etc.
    if normalize: 
        ax.set_ylabel("Normalized Scores")
        ax.set_yticks(np.arange(0, 1.2, 0.2))
    else: 
        ax.set_ylabel("Scores")
        ax.set_yticks(list(range(5)))
        
    # if normalize:
    #     ax.set_ylim([0, 1.2])
    # else:
    #     if iteration_idx == 6:
    #         ax.set_ylim([0, 4.4])
    #     elif iteration_idx == 7:
    #         ax.set_ylim([0, 4.7])
    max_multiplier = 1.5
    if iteration_idx == 7:
        max_multiplier = 1.4
    ax.set_ylim([0, max_bar*max_multiplier + max_err*1.2])
    ax.set_xticks(x, eval_categories)
    ax.set_xlabel("Evaluation categories")
    # ax.legend()
    fig.tight_layout()
    fig.set_size_inches(PLOT_WIDTH, PLOT_HEIGHT)

    if title:
        plt.title(title)

    partition_string = ""
    if partition_by:
        partition_string = f"{partition_by}{partition_operator}{partition_threshold}"
    
    if custom_name: 
        plt.savefig(f"it{iteration_idx}_{normalize=}_{partition_string}_{custom_name=}.png")
    else:
        if not partition_string:
            plt.title("Bot Evaluation Mean Results")
        else:
            plt.title(f"Bot Evaluation Mean Results ({partition_string})")
        plt.savefig(f"it{iteration_idx}_{normalize=}_{partition_string}_bot_mean_results.png")


def create_bot_box_plots(df: pd.DataFrame, iteration_idx: int = None, normalize: bool = False):
    if normalize:
        df = normalize_scores_by_user(df)

    eval_categories = sorted(list(set(SURVEY_QUESTIONS.values())))

    num_unique_workers = len(df.groupby("worker_id").agg(["count"]))
    logger.info(f"Number of unique workers in this iteration: {num_unique_workers}")

    cols_to_drop = ["worker_id", "messages"]
    df = df.drop(cols_to_drop, axis=1)

    print(
        df.groupby("bot_type").agg(["mean", "std", "count"])[eval_categories]
    )

    grouped_df = df.groupby("bot_type")[eval_categories]
    # rename the bot_types 
    grouped_df = grouped_df.rename(index={"moderator": "GPT-Moderator", "wisebeing": "GPT-NVC", "witty": "GPT-Witty", "stern": "GPT-Stern", "moderator-cosmo-xl": "Cosmo-XL", "moderator-prosocial": "Canary+Cosmo-XL", "socratic": "GPT-Socratic"})
    
    # reorder the bot_types
    bot_order = ["Cosmo-XL", "Canary+Cosmo-XL", "GPT-Moderator", "GPT-Stern", "GPT-Witty", "GPT-NVC", "GPT-Socratic"]

    x = np.arange(len(eval_categories))  # the label locations
    fig, ax = plt.subplots()
    number_of_bots = len(bot_order)

    colors = plt.cm.get_cmap('tab10', number_of_bots)
    legend_elements = []

    for idx, bot_type in enumerate(bot_order):
        group = grouped_df[bot_type]
        data = [group[cat] for cat in eval_categories]
        positions = x + idx * 0.25 / (number_of_bots - 1) - 0.125
        box_plot = ax.boxplot(data, positions=positions, widths=0.25 / number_of_bots, manage_ticks=False, patch_artist=True)

        for box in box_plot['boxes']:
            box.set_facecolor(colors(idx))

        legend_elements.append(Patch(facecolor=colors(idx), label=bot_order))

    # Add some text for labels, title and custom x-axis tick labels, etc.
    if normalize:
        ax.set_ylabel("Normalized Scores")
    else:
        ax.set_ylabel("Scores")

    ax.set_xticks(x, eval_categories)
    ax.set_xlabel("Evaluation categories")
    ax.legend(handles=legend_elements, title="Bot Types")
    
    plt.title("Bot Evaluation Mean Results")

    fig.tight_layout()
    fig.set_size_inches(PLOT_WIDTH, PLOT_HEIGHT)
    plt.savefig(f"it{iteration_idx}_{normalize=}_bot_mean_results_boxplot.png")



def create_task_per_worker_plot(df, iteration_idx=None): 

    tasks_done_by_each_worker = df.groupby("worker_id").agg(["count"])["topic_id"].sort_values(by="count", ascending=False)
    print(tabulate(tasks_done_by_each_worker))
    logger.info(f"Number of unique workers: {len(tasks_done_by_each_worker)}")
    n_bins = 20 
    fig, ax = plt.subplots()
    plt.hist(tasks_done_by_each_worker['count'].tolist(), n_bins)
    
    ax.set_ylabel("Number of workers")
    ax.set_xlabel("Tasks done by workers")
    fig.tight_layout()
    fig.set_size_inches(PLOT_WIDTH, PLOT_HEIGHT)

    plt.title("Worker - # Task distribution")
    plt.savefig(f"it{iteration_idx}_worker_task_histogram.png")


def t_test(df, iteration_idx, normalize):
    model_map = {"moderator": "GPT-Moderator", "wisebeing": "GPT-NVC", "witty": "GPT-Witty", "stern": "GPT-Stern", "moderator-cosmo-xl": "Cosmo-XL", "moderator-prosocial": "Canary+Cosmo-XL", "socratic": "GPT-Socratic"}
    if normalize: 
        if iteration_idx < 5: 
            metrics_to_normalize = ["coherency", "engaging", "understanding", "convincing", "human_words", "bot_words"]
        else: 
            metrics_to_normalize = ["specific", "fair", "engaging", "respectful", "agreement", "likeability", "human_words", "bot_words"]
        df = normalize_scores_by_user(df, metrics_to_normalize)
    score_dict = defaultdict(dict)
    for name, group in df.groupby('bot_type'):
        for metric in ["specific", "fair", "engaging", "respectful", "human_words", "bot_words"]:
            score_dict[metric][name] = group[metric].tolist()
    sig_diff = defaultdict(set)
    for metric, models_scores in score_dict.items():
        print()
        print(metric.upper())
        model_names = list(models_scores.keys())
        model_names_lens = [len(model_name) for model_name in model_names]
        print(f"{'':<20}", ''.join([f"{model_name:>{len(model_name)+4}}" for model_name in model_names]))
        for model_0, scores_0 in models_scores.items():
            ps = []
            for model_1, scores_1 in models_scores.items():
                if model_0 != model_1:
                    p = stats.ttest_ind(a=scores_0, b=scores_1, equal_var=True).pvalue
                    ps.append(p)
                    if model_0 == 'socratic':
                        if p < 0.05:
                            sig_diff[metric].add(model_map[model_1])
                else:
                    ps.append(-1)
            print(f"{model_0:<20}", ''.join([f"{ps[i]:>{model_names_lens[i]+4}.4f}" if ps[i] >=0 else f"{'':>{model_names_lens[i]+4}}" for i in range(len(ps))]))
    return sig_diff


def spearman_correlation(df):
    metrics = ["specific", "fair", "engaging", "respectful", "agreement", "likeability", "human_words", "bot_words"]
    for metric_0 in metrics:
        scores_0 = df[metric_0].tolist()
        rs, ps = [], []
        print(f"{'':<12}" + ''.join([f"{metric:>16}" for metric in metrics]))
        for metric_1 in metrics:
            if metric_0 != metric_1:
                scores_1 = df[metric_1].tolist()
                spearmanr = st.spearmanr(scores_0, scores_1)
                r = spearmanr.statistic
                p = spearmanr.pvalue
                rs.append(r)
                ps.append(p)
            else:
                rs.append(-100)
                ps.append(-100)
        print(f"{metric_0:<12}" + ''.join([f"{rs[i]:>8.4f}({ps[i]:.4f})" if rs[i] >= -10 else f"{'':<16}" for i in range(len(rs))]))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--iteration_idx", "-idx", type=int, default=3, help="iteration index: [1,2]"
    )
    parser.add_argument(
        "--normalize", "-n", action="store_true", help="normalize scores by user"
    )
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

    # breakpoint()
    dates_of_interest = ITERATION_DATES.get(args.iteration_idx, [])

    if not dates_of_interest:
        logger.warning(
            f"There were no dates identified for the given iteration index. Make sure that you have identified dates for iteration #{args.iteration_idx} and that they exist in {BASE_DATA_DIR}"
        )
    data_files = get_annotated_datafiles_for_dates(dates_of_interest)

    all_mturk_results = []
    for fn in data_files:
        try:
            mturk_result = extract_data_of_interest(fn, args.iteration_idx)
            if mturk_result:
                all_mturk_results += mturk_result
        except Exception as e:
            logger.exception(e)
            print(e)
            print(fn)

    df = pd.DataFrame(all_mturk_results)
    
    # drop problematic bots 
    if args.iteration_idx == 2: 
        bots_to_ignore = ["stern", "advocate"]
        df = df[~df['bot_type'].isin(bots_to_ignore)]
    
    # normalize scores by user 
    df = filter_users(df)

    # partition
    if args.partition_by is not None:
        df = df[OPS[args.partition_operator](df[args.partition_by], args.partition_threshold)]

    # t-test
    sig_diff = t_test(df, iteration_idx=args.iteration_idx, normalize=args.normalize)
                
    # spearmans correlation
    spearman_correlation(df)

    # plot
    create_bot_mean_plots(df, iteration_idx=args.iteration_idx, normalize=args.normalize, sig_diff=sig_diff, partition_by=args.partition_by, partition_threshold=args.partition_threshold, partition_operator=args.partition_operator)
    create_word_count_plots(df, iteration_idx=args.iteration_idx, normalize=args.normalize, sig_diff=sig_diff)
    create_task_per_worker_plot(df, iteration_idx=args.iteration_idx)
    