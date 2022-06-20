import os
from logging import Logger
import yaml
import redis
import praw
from typing import Dict
from praw.models import Redditor

CRED_FN = os.environ.get("CRED_FP", "/isi_darma/isi_darma/src/isi_darma/creds.yaml")


def get_username(redditor_obj: Redditor):
	"""
    Get the username of a redditor
    Redditor object reference: https://praw.readthedocs.io/en/latest/code_overview/models/redditor.html#praw.models.Redditor
    """
	return redditor_obj.author


def load_credentials(logger: Logger, creds_fn: str = CRED_FN) -> Dict[str, str]:
	with open(creds_fn, "r") as f:
		creds = yaml.safe_load(f)

	logger.debug(f"Loaded credentials: {creds}")
	return creds


def load_reddit_client(logger):
	creds = load_credentials(logger)

	reddit = praw.Reddit(
		user_agent=f"reddit:darma:0 (by u/{creds['username']})",
		client_id=creds["client_id"],
		client_secret=creds["client_secret"],
		username=creds["username"],
		password=creds["password"]
	)

	return reddit


def check_for_opt_out(comment_str: str) -> bool:
	"""
	Check if the comment contains the opt out phrase
	"""

	# Remove all non-alphanumeric characters
	comment_lower = comment_str.lower()
	if "opt out" in comment_lower or "optout" in comment_lower:
		return True

	return False

def add_to_db(redis_client: redis.Redis, username: str):
	"""
	Save the username to the redis store
	"""
	redis_client.set(username, "opted out")


def search_db(redis_client: redis.Redis, username: str):
	"""
	Search the redis store for the username
	"""
	# Return true if the username is in the store
	return redis_client.get(username) is not None