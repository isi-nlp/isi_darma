from isi_darma.utils import load_reddit_client
from typing import List 

reddit = load_reddit_client()

def format_dialogue(comment_list: List): 

    dialogues = [[comment] for comment in comment_list] 
    print(dialogues)
    while any([d[-1].replies for d in  dialogues]): 
        new_dialogues =[] 
        for d in dialogues: 
            if not isinstance(d[-1], str) and d[-1].replies: 
                new_dialogues += [d + [reply] for reply in d[-1].replies]
            else: 
                new_dialogues += [d] 
        # dialogues = [d[:-1] + [d[-1].body, reply] for d in dialogues for reply in d[-1].replies] 
        dialogues = new_dialogues
        print(dialogues)

    # transform everything into text 
    dialogues = [[comment.body for comment in d] for d in dialogues]

    return dialogues


url = "https://www.reddit.com/r/darma_test/comments/s8q5r6/spolin_you_so_crazy/"
submission = reddit.submission(url=url)

# subreddit = reddit.subreddit("darma_test")
# for submission in subreddit.stream.submissions():
submission.comments.replace_more(limit=None)
comment_queue = submission.comments[:]  # Seed with top-level
next_comment_level =[] 
print("_______new comment thread__________")
dialogues =format_dialogue(comment_queue)
print(dialogues)
            
import pdb; pdb.set_trace()

for d in dialogues: 
    print(d)

    # while comment_queue:
    #     comment = comment_queue.pop(0)
    #     print(comment.body)
    #     comment_queue.extend(comment.replies)