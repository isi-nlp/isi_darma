import os
from logging import Logger

import yaml
import praw
from typing import Dict
from praw.models import Redditor

CRED_FN = os.environ.get("CRED_FP", "/isi_darma/isi_darma/src/isi_darma/creds.yaml")


def get_username(redditor_obj: Redditor):
    """
    Get the username of a redditor
    Redditor object reference: https://praw.readthedocs.io/en/latest/code_overview/models/redditor.html#praw.models.Redditor
    """

    return redditor_obj.name


def load_credentials(logger: Logger, creds_fn: str = CRED_FN) -> Dict[str, str]:
    with open(creds_fn, "r") as f:
        creds = yaml.safe_load(f)

    logger.info(f"Loaded credentials: {creds}")
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
