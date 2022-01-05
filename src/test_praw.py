"""
Author: Justin Cho 

Testing Reddit API following instructions in https://yojji.io/blog/how-to-make-a-reddit-bot 
to programmatically create a post 
"""

import praw 
import yaml 

with open("creds.yaml", "r") as f: 
    creds = yaml.safe_load(f)

print(creds)

reddit = praw.Reddit(
    user_agent=f"reddit:darma:0 (by u/{creds['username']})",
    client_id=creds["client_id"],
    client_secret=creds["client_secret"], 
    username=creds["username"], 
    password=creds["password"]
)

title="First Test"
body="This is the first test with the Reddit API, creating a post programmatically."
reddit.subreddit("darma_test").submit(title=title, selftext=body)