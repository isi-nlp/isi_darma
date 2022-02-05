# temporary code for development 

from isi_darma.utils import load_reddit_client
from isi_darma.comments_utils import format_dialogue, get_dialogue_text
from isi_darma.pipeline.response_generators import SpolinBotRG
from typing import List 

reddit = load_reddit_client()

subreddit = reddit.subreddit("darma_test")
response_generator = SpolinBotRG()

for submission in subreddit.stream.submissions(): 
    title = submission.title
    post_body = submission.selftext

    print(title)
    print(post_body)

    submission.comments.replace_more(limit=None)
    comment_queue = submission.comments[:]  # Seed with top-level

    dialogues = format_dialogue(comment_queue)
    
    for d in dialogues: 
        d_text = get_dialogue_text(d)
        # response = response_generator.generate_response(incoming_dialogue=d_text)

# url = "https://www.reddit.com/r/darma_test/comments/s8q5r6/spolin_you_so_crazy/"
# submission = reddit.submission(url=url)

# submission.comments.replace_more(limit=None)
# comment_queue = submission.comments[:]  # Seed with top-level
# while comment_queue:
#     comment = comment_queue.pop(0)
#     print(comment.body)
#     comment_queue.extend(comment.replies)