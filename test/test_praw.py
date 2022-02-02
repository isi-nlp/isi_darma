"""
Author: Justin Cho 

Testing Reddit API following instructions in https://yojji.io/blog/how-to-make-a-reddit-bot 
to programmatically create a post 

Usage: python test_praw.py <title> <body> 
"""

import praw 
from isi_darma.utils import load_reddit_client
import sys 
from logging_setup import logger

title, body = sys.argv[1], sys.argv[2]
subreddit = "darma_test"

reddit_client = load_reddit_client()

# title="First Test"
# body="This is the first test with the Reddit API, creating a post programmatically."
logger.info(f"Posting to r/{subreddit}. \n\tTitle:\t{title}\n\tBody:\t{body}")
reddit_client.subreddit(subreddit).submit(title=title, selftext=body)