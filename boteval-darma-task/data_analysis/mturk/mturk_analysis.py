import json 
import numpy as np 
import pandas as pd 
from pathlib import Path 

mod_chats = [55, 784, 1014, 1068, 332, 410, 476, 51, 68, 132] 
nvc_chats = [1444, 1322, 1141, 570, 126, 858, 785, 696, 572, 444] 

survey_questions = {
    "How Coherent was the conversation?": "coherency",
    "How likely are you to continue chatting with the moderator?": "engaging",
    "To what degree did the moderator understand your point of view?": "understanding",
    "To what degree did the moderator convince you to change your behavior?": "convincing"
}

score_mapping = {
    'Not at all': 0, 
    'Mostly not': 1, 
    'So-so': 2, 
    'Somewhat': 3, 
    'Very': 4
}

base_data_dir = "/home/darma/work/boteval.prod/darma-task/data-prod/data/"

dates = [20230107, 20230108, 20230109]
# dates = [20230201, 20230202, 20230203, 20230204, 20230205, 20230206, 20230207] 

data_folders = [p for p in Path(base_data_dir).glob("*") if int(p.name) in dates]
data_files = [] 
for folder in data_folders: 
    fns = folder.glob("*.json")
    data_files.extend(fns)
    
len(data_files)

def get_data_of_interest(mturk_fn): 
    
    with open(mturk_fn) as f: 
        data = json.load(f)

    # chat number 
    chat_num = mturk_fn.name.split("chat")[-1].split("_")[0]

    # get ratings
    ratings= data['data']['ratings']
    ratings = {survey_questions[k]: int(v) for k, v in ratings.items()}
    # get user 
    worker_id = data['data']['mturk']['worker_id']
    #get bot type:
    bot_type = "Moderator bot" if int(chat_num) in mod_chats else "NVC bot"
    if bot_type == "NVC bot": 
        assert int(chat_num) in nvc_chats, chat_num 

    # get conversation 
    messages = data['messages']
    
    chat_num, bot_type, worker_id, ratings
    return {
        "topic_id": chat_num, 
        "bot_type": bot_type, 
        "worker_id": worker_id, 
        "messages" : messages, 
        **ratings
    }

pd_list = [ get_data_of_interest(fn) for fn in data_files ] 
pd_list[0]['messages']

def get_human_bot_number_words(messages):
    human = 0 
    bot = 0 
    for msg in messages: 
        if msg['user_id'] == "context": 
            continue 
        if msg['user_id'] == "bot01": 
            bot += len(msg['text'].split())
        else: 
            human += len(msg['text'].split())
            
    return human, bot 

get_human_bot_number_words(pd_list[0]['messages'])
            
for list_item in pd_list: 
    human, bot = get_human_bot_number_words(list_item['messages'])
    list_item["human_words"] = human 
    list_item["bot_words"] = bot 
    
pd.set_option('display.max_colwidth', -1)
df.groupby("bot_type").agg(["mean", "median", "std", "count"])[['coherency', 'engaging', 'understanding', 'convincing']]

# word count comparison 
df.groupby("bot_type").agg(["mean", "median", "std", "count"])[['human_words', 'bot_words']]

df = pd.DataFrame(pd_list)

df.groupby("worker_id").agg(["count"])['topic_id']

pd.set_option('display.max_colwidth', -1)
df.groupby("bot_type").agg(["mean", "median", "std", "count"])[['coherency', 'engaging', 'understanding', 'convincing']]

mean_results ={} 
for row in df.groupby("bot_type").agg(["mean", "count"]).iterrows(): 
    mean_results[row[0]] = {
        'coherency': row[1]['coherency']['mean'],
        'engaging': row[1]['engaging']['mean'],
        'understanding': row[1]['understanding']['mean'],
        'convincing': row[1]['convincing']['mean']
    }
    # print(row[1]['coherency']['mean'])
    
    
import matplotlib.pyplot as plt
import numpy as np

labels = list(survey_questions.values()) 
nvc_mean = [round(mean_results["NVC bot"][prop], 2) for prop in labels]
moderator_mean = [round(mean_results["Moderator bot"][prop],2) for prop in labels]

x = np.arange(len(labels))  # the label locations
width = 0.35  # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(x - width/2, nvc_mean, width, label='NVC Bot')
rects2 = ax.bar(x + width/2, moderator_mean, width, label='Moderator Bot')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Scores [0-4]')
ax.set_xticks(x, labels)
ax.legend()

ax.bar_label(rects1, padding=3)
ax.bar_label(rects2, padding=3)

fig.tight_layout()

plt.show()