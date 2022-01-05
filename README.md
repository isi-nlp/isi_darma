# DARMA ISI 


### Reddit API 

To use the Reddit API, you need the following parameters: 
```
reddit = praw.Reddit(
    user_agent="",
    client_id="",
    client_secret="", 
    username="", 
    password=""
)
```

- ‘user_agent’ can be anything, but the recommended format is <platform>:<app ID>:<version string> (by u/<Reddit username>)
- You can find the `client_id`, `client_secret` in https://www.reddit.com/prefs/apps/. 
- The username and password is the reddit account's username and password. Ask Justin for the username and password. 

A simple script that creates a post can be found in `src/test_praw.py`.  


References
1. [How To Make A Reddit Bot?](https://yojji.io/blog/how-to-make-a-reddit-bot)

