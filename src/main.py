from isi_darma.utils import load_reddit_client
from isi_darma.bots import BasicBot

from argparse import ArgumentParser

SUBREDDIT = "darma_test"


def main():
    parser = ArgumentParser()
    parser.add_argument("--test", "-t", action="store_true")
    args = parser.parse_args()

    moderation_bot = BasicBot(test=args.test)

    reddit_client = load_reddit_client(moderation_bot.logger)
    moderation_bot.logger.info("Instantiated Reddit Client")

    subreddit = reddit_client.subreddit(SUBREDDIT)
    posts = subreddit.stream.submissions(pause_after=-1)
    cmts = subreddit.stream.comments(pause_after=-1, skip_existing=True)
    # stream = praw.models.util.stream_generator(stream_all(subreddit))

    while True:
        for post in posts:
            if post is None:
                break
            # print("POST: ", post.title)
            moderation_bot.moderate_submission(post)

        for cmt in cmts:
            if cmt is None:
                break
            # print("CMT: ", cmt.body[:50])
            moderation_bot.moderate_comment_thread(cmt)
            # moderation_bot.moderate_submission(cmt, title=cmt.submission.title, post_body=cmt.submission.selftext)

    # for idx, submission in enumerate(stream):
    # 	print(idx+1, submission.body)
        # moderation_bot.moderate_submission(submission)


if __name__ == "__main__":
    main()
