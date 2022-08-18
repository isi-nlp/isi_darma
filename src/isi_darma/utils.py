import os
from logging import Logger
import yaml
import re
import json
import praw
from typing import Dict
from praw.models import Redditor

CRED_FN = os.environ.get("CRED_FP", "/isi_darma/isi_darma/src/isi_darma/creds.yaml")


def get_username(redditor_obj: Redditor):
	"""
    Get the username of a redditor
    Redditor object reference: https://praw.readthedocs.io/en/latest/code_overview/models/redditor.html#praw.models.Redditor
    """
	return redditor_obj.author.name if redditor_obj else ''


def get_post_id(redditor_obj: Redditor):
	return redditor_obj.id if redditor_obj else ''


def load_credentials(logger: Logger, creds_fn: str = CRED_FN) -> Dict[str, str]:
	with open(creds_fn, "r") as f:
		creds = yaml.safe_load(f)

	logger.debug(f"Loaded credentials from {creds_fn}")
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

	# Remove all non-alphanumeric characters using regex
	comment_alphanum = re.sub('[\W_]+', '', comment_str)

	# Covert comment to lowercase
	comment_lower = comment_alphanum.lower()

	if "opt out" in comment_lower or "optout" in comment_lower:
		return True

	return False


# TODO: List of changes needed in data collection:
# 1. Save the structure of the thread in the json - refer Apoorva's code and use as plug & play
# 2. Save the comment/post id in the json
# 3. Save the french comment and the translation in the json structure
def get_replied_to(comment) -> str:
		this_comment = comment

		if isinstance(this_comment.parent(), type(comment)) or isinstance(this_comment.parent(), type(comment.submission)):
			return " towards " + this_comment.parent().author.name
		else:
			return ""

def get_child_comments(logger, currComment, commentList, botReply, postedComment):
		"""
		Helper method for create_json_thread()
		"""
		if not currComment.replies._comments:
			return
		else:
			myComments = currComment.replies._comments

			for x in myComments:

				try:
					myAuthor = x.author.fullname
					addComment = [myAuthor, x.body]
				except AttributeError:
					myAuthor = "[Author of deleted post.]"
					addComment = [myAuthor, "<empty>"]
					logger.debug(f"Looking for author of deleted post/comment. Comment set to - {addComment}")
					commentList.append(addComment)
					return

				commentList.append(addComment)
				get_child_comments(logger, x, commentList, botReply, postedComment)

				if x == postedComment:
					addComment = ["DarmaBot", botReply]
					commentList.append(addComment)

# TODO: List of changes needed in data collection:
# 1. Save the structure of the thread in the json - refer Apoorva's code and use as plug & play
# 2. Save the comment/post id in the json
# 3. Save the french comment and the translation in the json structure
def create_json_thread(logger, comment, is_submission, bot_reply, subreddit = "darma_test"):
	"""
	Records entire conversation tree into JSON format
	"""

	comment_list = []

	this_submission = comment

	if not is_submission:
		this_submission = comment.submission

	add_submission = [this_submission.author.fullname, this_submission.selftext]
	comment_list.append(add_submission)

	my_comments = this_submission.comments._comments

	for this_comment in my_comments:

		try:
			my_author = this_comment.author.fullname
			addComment = [my_author, this_comment.body]
		except AttributeError:
			my_author = "[Author of deleted post.]"
			addComment = [my_author, "<empty>"]
			logger.debug(f"Looking for author of deleted post/comment. Comment set to - {addComment}")

		add_comment = [my_author, this_comment.body]
		comment_list.append(add_comment)
		get_child_comments(logger, this_comment, comment_list, bot_reply, comment)

		if this_comment == comment:
			add_comment = ["DarmaBot", bot_reply]
			comment_list.append(add_comment)

	my_conversation = []

	for x in comment_list:
		new_utterance = {"speaker_id": x[0], "text": x[1]}
		my_conversation.append(new_utterance)

	data = {"conversation": my_conversation, "target_user": comment.author.fullname}

	json_outputs_path = "/isi_darma/isi_darma/src/isi_darma/data/conversations"
	if not os.path.exists(json_outputs_path):
		os.makedirs(json_outputs_path)

	size = len(os.listdir(json_outputs_path))
	filename = f"{json_outputs_path}/{subreddit}_conversationDump{size}.json"
	with open(filename, "w") as write_file:
		json.dump(data, write_file, indent=4)
	write_file.close()
	logger.debug(f"Saved conversation to {filename}")
