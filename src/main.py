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

	for submission in subreddit.stream.submissions():
		moderation_bot.moderate_submission(submission)

	return


if __name__ == "__main__":
	main()
