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
import numpy as np
from tabulate import tabulate
from loguru import logger
from argparse import ArgumentParser

BASE_DATA_DIR = "/home/darma/work/boteval.prod/darma-task/data-prod/data/"

SURVEY_QUESTIONS = {
    "how coherent was the conversation?": "coherency",
    "how likely are you to continue chatting with the moderator?": "engaging",
    "to what degree did the moderator understand your point of view?": "understanding",
    "to what degree did the moderator convince you to change your behavior?": "convincing",
}

ITERATION1_MOD_CHATS = [55, 784, 1014, 1068, 332, 410, 476, 51, 68, 132]
ITERATION1_NVC_chats = [1444, 1322, 1141, 570, 126, 858, 785, 696, 572, 444]
ITERATION_DATES = {
    1: [20230107, 20230108, 20230109],
    2: [20230201, 20230202, 20230203, 20230204, 20230205, 20230206, 20230207, 20230208],
}

PLOT_WIDTH=12
PLOT_HEIGHT=8

def extract_bot_type(endpoint: str) -> str:
    persona_configs = json.load(
        open("/home/darma/work/boteval.prod/darma-task/persona_configs.json")
    )
    persona_names = [c["id"] for c in persona_configs]

    for name in persona_names:
        if name in endpoint:
            return name
    return None


def get_annotated_data_for_dates(dates: List[str]) -> List[str]:
    data_folders = [p for p in Path(BASE_DATA_DIR).glob("*") if int(p.name) in dates]
    data_files = []
    for folder in data_folders:
        fns = folder.glob("*.json")
        data_files.extend(fns)

    logger.info(f"# of data files found: {len(data_files)}")
    return data_files


def extract_data_of_interest(mturk_fn: str, iteration_idx=None) -> Dict[str, Any]:
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

    # get ratings
    ratings = data["data"]["ratings"]
    ratings = {
        SURVEY_QUESTIONS[k.lower()]: int(v)
        for k, v in ratings.items()
        if k != "optional_feedback"
    }

    # get user
    if "mturk_sandbox" in data["data"]:
        return None

    worker_id = data["data"]["mturk"]["worker_id"]

    if iteration_idx == 1:
        bot_type = "moderator" if int(chat_num) in ITERATION1_MOD_CHATS else "wisebeing"
        if bot_type == "wisebeing":
            assert int(chat_num) in ITERATION1_NVC_chats, chat_num
    else:
        # hacky way to do it for second iteration TODO: store bot type into collected data
        bot_type = extract_bot_type(data["users"][0]["data"]["next"])

    # get conversation
    messages = data["messages"]

    return {
        "topic_id": chat_num,
        "bot_type": bot_type,
        "worker_id": worker_id,
        "messages": messages,
        **ratings,
    }


def get_human_bot_number_words(messages):
    human = 0
    bot = 0
    for msg in messages:
        if msg["user_id"] == "context":
            continue
        if msg["user_id"] == "bot01":
            bot += len(msg["text"].split())
        else:
            human += len(msg["text"].split())

    return human, bot


def create_word_count_plots(df, iteration_idx=None): 

    categories_of_interest = ["human_words", "bot_words"]
    agg_by_bots = df.groupby("bot_type").agg(["mean", "median", "std", "count"])[
        categories_of_interest
    ]
    means_by_bot_type = {}
    for row in agg_by_bots.iterrows():
        means_by_bot_type[row[0]] = [round(row[1][l]["mean"], 2) for l in categories_of_interest]

    x = np.arange(len(categories_of_interest))  # the label locations

    fig, ax = plt.subplots()
    number_of_bots = len(means_by_bot_type)
    width = 1 / number_of_bots * 1.7
    start_width = x - width * number_of_bots / 4
    for idx, (bot_type, means) in enumerate(means_by_bot_type.items()):
        bot_count = int(agg_by_bots.loc[bot_type][categories_of_interest[0]]['count'])
        rects1 = ax.bar(start_width, means, width / 2, label=f"{bot_type} [{bot_count}]")
        start_width += width / 2
        ax.bar_label(rects1, padding=3)

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel("Word count")
    ax.set_xticks(x, categories_of_interest)
    ax.legend()

    fig.tight_layout()
    fig.set_size_inches(PLOT_WIDTH, PLOT_HEIGHT)
    fig.savefig(f"it{iteration_idx}_words_mean_results.png", dpi=100)

def create_bot_mean_plots(df, iteration_idx=None): 
    
    eval_categories = sorted(list(SURVEY_QUESTIONS.values()))

    print(
        tabulate(df.groupby("bot_type").agg(["mean", "count"])[eval_categories])
    )
    
    num_unique_workers = len(df.groupby("worker_id").agg(["count"]))
    logger.info(f"Number of unique workers in this iteration: {num_unique_workers}")

    import pdb ; pdb.set_trace()

    agg_by_bots = df.groupby("bot_type").agg(["mean", "median", "std", "count"])[eval_categories]
    means_by_bot_type = {}
    for row in agg_by_bots.iterrows():
        means_by_bot_type[row[0]] = [round(row[1][l]["mean"], 2) for l in eval_categories]
    
    x = np.arange(len(eval_categories))  # the label locations
    fig, ax = plt.subplots()
    number_of_bots = len(means_by_bot_type)
    width = 1 / number_of_bots * 1.5
    start_width = x - width * number_of_bots / 4
    
    for idx, (bot_type, means) in enumerate(means_by_bot_type.items()):
        bot_count = int(agg_by_bots.loc[bot_type][eval_categories[0]]['count'])
        stds = [agg_by_bots.loc[bot_type][cat]['std'] for cat in eval_categories]
        rects1 = ax.bar(start_width, means, width / 2, label=f"{bot_type} [{bot_count}]")
        
        ax.errorbar(start_width, means, stds, linestyle='None', markeredgecolor="black", ecolor="black",  fmt='-o')

        start_width += width / 2
        ax.bar_label(rects1, padding=3)

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel("Scores [1-5]")
    ax.set_ylim([1, 5])
    ax.set_xticks(x, eval_categories)
    ax.set_xlabel("Evaluation categories")
    ax.legend()

    plt.title("Bot Evaluation Mean Results")

    fig.tight_layout()
    fig.set_size_inches(PLOT_WIDTH, PLOT_HEIGHT)
    plt.savefig(f"it{iteration_idx}_bot_mean_results.png")


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
    

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--iteration_idx", "-idx", type=int, default=1, help="iteration index: [1,2]"
    )
    args = parser.parse_args()

    dates_of_interest = ITERATION_DATES.get(args.iteration_idx, [])

    if not dates_of_interest:
        logger.warning(
            f"There were no dates identified for the given iteration index. Make sure that you have identified dates for iteration #{args.iteration_idx} and that they exist in {BASE_DATA_DIR}"
        )
    data_files = get_annotated_data_for_dates(dates_of_interest)

    all_mturk_results = []
    for fn in data_files:
        try:
            mturk_result = extract_data_of_interest(fn, args.iteration_idx)
            if mturk_result:
                all_mturk_results.append(mturk_result)
        except Exception as e:
            print(e)
            print(fn)

    # add information about the number of words for human / bot actors
    for list_item in all_mturk_results:
        human, bot = get_human_bot_number_words(list_item["messages"])
        list_item["human_words"] = human
        list_item["bot_words"] = bot

    df = pd.DataFrame(all_mturk_results)
    create_bot_mean_plots(df, iteration_idx=args.iteration_idx)
    create_word_count_plots(df, iteration_idx=args.iteration_idx)
    create_task_per_worker_plot(df, iteration_idx=args.iteration_idx)
    