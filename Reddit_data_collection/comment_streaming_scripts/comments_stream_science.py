#!/usr/bin/env python3

import json
import pandas as pd
import praw
import prawcore
import time, datetime

credentials = '/nas/home/asharma/ISI_reddit/client_secret.json'
with open(credentials) as f:
    creds = json.load(f)

reddit = praw.Reddit(client_id = creds['client_id'],
                    client_secret = creds['client_secret'],
                    user_agent = creds['user_agent'],
                    redirect_uri = creds['redirect_uri'],
                    refresh_token = creds['refresh_token'])

subreddit = reddit.subreddit("science")

comments = pd.DataFrame()
counter = 0

timeout = time.time() + 60*60 #1hr

print("Start time:", datetime.datetime.now().strftime("%d_%b_%Y_%H_%M_%S"), "__SCIENCE__ Comments")

while True:
  try:
    for comment in subreddit.stream.comments(skip_existing=True):
      com_dict = {}
      
      com_dict['id'] = comment.id
      com_dict['parent_id'] = comment.parent_id
      com_dict['link_id'] = comment.link_id
      com_dict['body'] = comment.body
      com_dict['collapsed'] = comment.collapsed
      com_dict['score'] = comment.score
      com_dict['controversiality'] = comment.controversiality
      com_dict['permalink'] = comment.permalink
      com_dict['created_utc'] = comment.created_utc
      if comment.author != None:
        com_dict['author'] = comment.author.id
      else:
        com_dict['author'] = "Not found"

      comments = comments.append(com_dict, ignore_index=True, sort=False)
      counter = counter + 1

      if time.time() > timeout:
        print("------Collected "+ str(counter) + " comments in one hour for subreddit __SCIENCE__")

        comments.to_csv('/data/asharma/science/com_stream_science.csv', mode='a', header=False, index=False, columns=list(comments.axes[1]))
        
        timeout = time.time() + 60*60
        comments = pd.DataFrame()
        counter = 0
  except Exception as err:
    print(f'{err}. Sleeping for 10 seconds...  __SCIENCE__ Comments')
    time.sleep(10)