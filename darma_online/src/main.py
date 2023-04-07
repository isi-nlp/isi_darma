from darma_online.utils import load_reddit_client, build_logger
from darma_online.bots import BasicBot

import time
import prawcore.exceptions
from argparse import ArgumentParser

SUBREDDIT = "darma_test"


def main():
    parser = ArgumentParser()
    parser.add_argument("--test", "-t", action="store_true")
    parser.add_argument("--passive", "-p", action="store_true")
    parser.add_argument("--mod_assist", "-m", default=True, required=True)
    parser.add_argument("--subreddit", "-s", default=SUBREDDIT)
    parser.add_argument("--lang", "-l", default="english", required=True)
    args = parser.parse_args()

    # Set the subreddit to be moderated
    sub_name = SUBREDDIT if args.subreddit is None else args.subreddit
    logger = build_logger(sub_name, test=args.test)

    reddit_client = load_reddit_client(logger)
    logger.info(f"Instantiated Reddit Client with {args.passive=}, {args.test=}, {args.subreddit=}")

    subreddit = reddit_client.subreddit(sub_name)
    mods_list = [moderator.name for moderator in subreddit.moderator()]
    posts = subreddit.stream.submissions(pause_after=-1, skip_existing=True)
    cmts = subreddit.stream.comments(pause_after=-1, skip_existing=True)
    logger.info(f"Instantiated Subreddit {sub_name} with {len(mods_list)} moderators -> {mods_list}")

    moderation_bot = BasicBot(reddit_client=reddit_client,
                              test=args.test,
                              passive=args.passive,
                              sub_name=sub_name,
                              sub_obj = subreddit,
                              lang=args.lang,
                              mod_assist=args.mod_assist,
                              logger=logger)

    while True:
        try:
            for post in posts:
                if post is None:
                    break
                # print("POST: ", post.title)
                moderation_bot.moderate_submission(post)

            for cmt in cmts:
                if cmt is None:
                    break
                # print("CMT: ", cmt.title)
                moderation_bot.moderate_comment_thread(cmt)

        # In case of server error from praw, give some time for reddit to recover and try again.
        except prawcore.exceptions.ServerError as server_error:
            moderation_bot.logger.warning(f"Reddit Server error: {server_error}. Waiting for 30 seconds.")
            time.sleep(30)
            continue

        except Exception as e:
            moderation_bot.logger.error(f"Exception occurred while streaming posts and comments: {e}", exc_info=True)
            continue


if __name__ == "__main__":
    main()
