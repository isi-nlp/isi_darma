from darma_online.utils import load_reddit_client
from darma_online.bots import BasicBot

import time
import prawcore.exceptions
from argparse import ArgumentParser

SUBREDDIT = "darma_test"


def main():
	parser = ArgumentParser()
	parser.add_argument("--test", "-t", action="store_true")
	parser.add_argument("--passive", "-p", action="store_true")
	parser.add_argument("--subreddit", "-s", default=SUBREDDIT, required=False)
	args = parser.parse_args()

	# Set the subreddit to be moderated
	sub = SUBREDDIT if args.subreddit is None else args.subreddit

	moderation_bot = BasicBot(test=args.test, passive=args.passive, sub=sub)

	reddit_client = load_reddit_client(moderation_bot.logger)
	moderation_bot.logger.info(f"Instantiated Reddit Client with {args.passive=}, {args.test=}, {args.subreddit=}")

	subreddit = reddit_client.subreddit(sub)
	posts = subreddit.stream.submissions(pause_after=-1, skip_existing=True)
	cmts = subreddit.stream.comments(pause_after=-1, skip_existing=True)
	moderation_bot.logger.info("Instantiated Subreddit stream for posts and comments")

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