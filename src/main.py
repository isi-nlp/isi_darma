from isi_darma.logging_setup import logger
from isi_darma.utils import load_reddit_client
from isi_darma.bots import BasicBot

from argparse import ArgumentParser

logger.info("\n\n\n")
SUBREDDIT = "darma_test"


def main():
	parser = ArgumentParser()
	parser.add_argument("--test", "-t", action="store_true")
	args = parser.parse_args()

	reddit_client = load_reddit_client()
	logger.info("Instantiated Reddit Client")

	moderation_bot = BasicBot(test=args.test)

	subreddit = reddit_client.subreddit(SUBREDDIT)

	for submission in subreddit.stream.submissions():
		moderation_bot.moderate_submission(submission)

	return


if __name__ == "__main__":
	main()
