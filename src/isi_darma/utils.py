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
	return redditor_obj.author if redditor_obj else ''


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


def read_db(path : str = "isi_darma/data/optout/optout_db.json"):
	"""
	Read the json file for opt-out users
	"""
	return json.loads(open(path, "r").read())


def add_to_db(db : dict, username: str, toxicity_score: float, behav_type: str):
	"""
	Save the username to the redis store
	"""
	db[username] = {
					'toxicity_score' : toxicity_score,
	                'behav_type': behav_type
				   }

	with open("db.json", "w") as f:
		f.write(json.dumps(db))

	return db

def user_in_db(db : dict, username: str):
	"""
	Search the redis store for the username
	"""
	return True if username in db.keys() else False


def read_responses(path : str = "isi_darma/data/response_templates/responses.json"):
	"""
	Read the json file for bot info.
	"""
	return json.loads(open(path, "r").read())

def get_replied_to(comment) -> str:
		this_comment = comment

		if isinstance(this_comment.parent(), type(comment)) or isinstance(this_comment.parent(), type(comment.submission)):
			return " towards " + this_comment.parent().author.name
		else:
			return ""

def get_child_comments(currComment, commentList, botReply, postedComment):
		"""
		Helper method for create_json_thread()
		"""
		if not currComment.replies._comments:
			return
		else:
			myComments = currComment.replies._comments
			for x in myComments:
				myAuthor = "[Author of deleted post.]"
				if x.author is not None:
					myAuthor = x.author.fullname
				addComment = [myAuthor, x.body]
				commentList.append(addComment)
				get_child_comments(x, commentList, botReply, postedComment)

				if x == postedComment:
					addComment = ["DarmaBot", botReply]
					commentList.append(addComment)

def create_json_thread(comment, is_submission, bot_reply):
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
		my_author = "[Author of deleted post.]"
		if this_comment.author is not None:
			my_author = this_comment.author.fullname
		add_comment = [my_author, this_comment.body]
		comment_list.append(add_comment)
		get_child_comments(this_comment, comment_list, bot_reply, comment)

		if this_comment == comment:
			add_comment = ["DarmaBot", bot_reply]
			comment_list.append(add_comment)


	my_conversation = []

	for x in comment_list:
		new_utterance = {}
		new_utterance["speaker_id"] = x[0]
		new_utterance["text"] = x[1]
		my_conversation.append(new_utterance)

	data = {}
	data["conversation"] = my_conversation
	data["target_user"] = comment.author.fullname

	json_outputs_path = "json_outputs"
	if not os.path.isdir(json_outputs_path):
		os.mkdir(json_outputs_path)

	size = len(os.listdir(json_outputs_path))

	json_outputs_path = os.path.join(json_outputs_path, "conversationDump" + str(size) + ".json")
	with open(json_outputs_path, "w") as write_file:
		json.dump(data, write_file, indent=4)
	write_file.close()