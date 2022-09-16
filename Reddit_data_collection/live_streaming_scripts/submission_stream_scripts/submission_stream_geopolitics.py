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

subreddit = reddit.subreddit("geopolitics")

submissions = pd.DataFrame()
counter = 0

timeout = time.time() + 60*60 #1hr

print("Start time:", datetime.datetime.now().strftime("%d_%b_%Y_%H_%M_%S"), "__GEOPOLITICS__ Posts")

while True:
  try:
    for submission in subreddit.stream.submissions(skip_existing=True):
      sub_dict = {}

      sub_dict['id'] = submission.id
      sub_dict['title'] = submission.title
      sub_dict['selftext'] = submission.selftext
      sub_dict['score'] = submission.score
      sub_dict['upvote_ratio'] = submission.upvote_ratio
      sub_dict['num_comments'] = submission.num_comments
      sub_dict['permalink'] = submission.permalink
      sub_dict['created_utc'] = submission.created_utc
      if submission.author != None:
        sub_dict['author'] = submission.author.id
      else:
        sub_dict['author'] = "Not found"

      submissions = submissions.append(sub_dict, ignore_index=True, sort=False)
      counter = counter + 1

      if time.time() > timeout:
        print("------Collected "+ str(counter) + " posts in one hour for subreddit __GEOPOLITICS__")

        submissions.to_csv('/nas/home/asharma/data/geopolitics/sub_stream_geopolitics.csv', mode = 'a', header=False, index=False, columns=list(submissions.axes[1]))

        timeout = time.time() + 60*60
        submissions = pd.DataFrame()
        counter = 0
  except Exception as err:
    print(err, 'Sleeping for 10 seconds...  __GEOPOLITICS__ Posts')
    time.sleep(10)