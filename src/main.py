from isi_darma.utils import load_reddit_client
from isi_darma.bots import BasicBot
from time import sleep

from argparse import ArgumentParser

SUBREDDIT = "darma_test"


def main(test=False):
	parser = ArgumentParser()
	parser.add_argument("--test", "-t", action="store_true")
	args = parser.parse_args()

	moderation_bot = BasicBot(test=args.test)

	reddit_client = load_reddit_client(moderation_bot.logger)
	moderation_bot.logger.info("Instantiated Reddit Client")

	while True:

		subreddit = reddit_client.subreddit(SUBREDDIT)
		for submission in subreddit.stream.submissions():
			moderation_bot.moderate_submission(submission)

		# moderation_bot.logger.info(f'------------ NO MORE POSTS/COMMENTS TO RESPOND TO! SLEEPING NOW... ------------')
		# sleep(15*60)


if __name__ == "__main__":
	main()
