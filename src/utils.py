import yaml
from loguru import logger
from typing import Dict
import praw
from praw.models import Redditor


def get_username(redditor_obj: Redditor):
    """
    Get the username of a redditor
    Redditor object reference: https://praw.readthedocs.io/en/latest/code_overview/models/redditor.html#praw.models.Redditor
    """

    return redditor_obj.name


def load_credentials(creds_fn: str = "creds.yaml") -> Dict[str, str]:
    with open(creds_fn, "r") as f:
        creds = yaml.safe_load(f)

    logger.info(f"Loaded credentials: {creds}")
    return creds


def load_reddit_client():
    creds = load_credentials()

    reddit = praw.Reddit(
        user_agent=f"reddit:darma:0 (by u/{creds['username']})",
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        username=creds["username"],
        password=creds["password"]
    )

    return reddit


# TODO: Add handler for creating log files
def setup_logger():
    pass
