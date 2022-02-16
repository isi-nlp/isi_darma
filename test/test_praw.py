"""
Author: Justin Cho 

Testing Reddit API following instructions in https://yojji.io/blog/how-to-make-a-reddit-bot 
to programmatically create a post 

Usage: python test_praw.py <title> <body> 
"""

import praw 
from isi_darma.utils import load_reddit_client
import sys 
from isi_darma.logging_setup import logger

title, body = sys.argv[1], sys.argv[2]


SUBREDDIT = "darma_test"

reddit_client = load_reddit_client()

# title="First Test"
# body="This is the first test with the Reddit API, creating a post programmatically."
# logger.info(f"Posting to r/{SUBREDDIT}. \n\tTitle:\t{title}\n\tBody:\t{body}")
# reddit_client.subreddit(SUBREDDIT).submit(title=title, selftext=body)


subreddit = reddit_client.subreddit(SUBREDDIT)

for submission in subreddit.stream.submissions():
    title = submission.title
    post_body = submission.selftext

    print(title)
    print(post_body)
    # submission.reply()