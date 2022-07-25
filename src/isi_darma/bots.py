import json
import os
from abc import ABC, abstractmethod
from imp import init_builtin
from numpy import empty
from isi_darma.comments_utils import format_dialogue
from isi_darma.logging_setup import setup_logger
from isi_darma.pipeline.moderation_classifiers import PerspectiveAPIModerator
from isi_darma.pipeline.response_generators import SpolinBotRG
from isi_darma.pipeline.translators import Translator
from isi_darma.utils import load_credentials, get_username, get_replied_to, create_json_thread

class ModerationBot(ABC):

	@abstractmethod
	def moderate(self):
		pass

	@abstractmethod
	def determine_moderation_strategy(self):
		pass


class BasicBot(ModerationBot):

	def __init__(self, reddit_client=None, test=False) -> None:
		super().__init__()

		self.test = test  # whether to actually post things to reddit

		# Setup logger based on the 'test' flag
		if not self.test:
			self.logger = setup_logger('app', 'logs/app.log', test=self.test)
		else:
			self.logger = setup_logger('test', 'logs/test.log', test=self.test)

		self.logger.info("\n\n\n -------- STARTING NEW INSTANCE -------- \n\n\n")
		self.reddit_client = reddit_client
		self.response_generator = SpolinBotRG(self.logger)
		self.translator = Translator(self.logger)
		self.moderation_classifier = PerspectiveAPIModerator(self.logger)
		self.CREDS = load_credentials(self.logger)
		self.current_dialogue = None
		self.toxic_users = set()

	@staticmethod
	def detect_language(text):
		return "english"

	def translate(self, text):
		return self.translator.rtg(text)

	def determine_moderation_strategy(self, comment_str: str):
		return "respond"

	def generate_response(self, dialogue):
		return self.response_generator.generate_response(dialogue)

	def moderate_submission(self, submission):

		title = submission.title
		post_body = submission.selftext

		submission.comments.replace_more(limit=None)
		comment_queue = submission.comments[:]  # Seed with top-level

		# check that we didn't already moderate the post
		if all([get_username(comment) != self.CREDS["username"] for comment in comment_queue]):
			self.moderate_post(submission)

		# dialogues is a list of comment objects
		dialogues = format_dialogue(comment_queue)
		for d in dialogues:
			last_comment = d[-1]
			username = get_username(last_comment)
			if username == self.CREDS["username"]:
				continue
			self.moderate_comment_thread(last_comment, title=title, post_body=post_body)

	def moderate_post(self, submission):
		"""
		Process post before sending to moderate function
		"""
		title = submission.title
		post_body = submission.selftext
		self.logger.info(f'Moderating the POST "{title}" now....')

		first_turn = f"{title} {post_body}".strip()
		translated_dialogue = self.translator.rtg(first_turn)
		botReply = self.moderate(translated_dialogue, submission)
		
		create_json_thread(submission, True, botReply)
		
	def moderate_comment_thread(self, dialogue, title="", post_body=""):
		"""
		Process comment thread before sending to moderate function
		"""
		last_comment = dialogue

		textComment = last_comment.body.lower().strip()
		if get_username(last_comment) != self.CREDS["username"]:
			self.logger.info(f'Moderating the COMMENT THREAD: {last_comment.body}')

			# self.current_dialogue = dialogue
			# dialogue_text = get_dialogue_text(dialogue)
			# self.logger.debug(f"Retrieved dialogue: {dialogue_text}")

			source_language = self.detect_language(last_comment.body)
			self.logger.debug(f"Translating all turns in dialogue")
			translated_dialogue = self.translator.rtg(last_comment.body)

			# if title or post_body:
			# 	first_turn = f"{title} {post_body}".strip()
			# 	translated_dialogue = [self.translator.rtg(first_turn)] + translated_dialogue

			self.logger.debug(f"Received Translated dialogue: {translated_dialogue}")
			botReply = self.moderate(translated_dialogue, last_comment)
			create_json_thread(last_comment, False, botReply)

		else:
			self.logger.debug(f'Self comment -> {last_comment.body} with username: {get_username(last_comment)}')

	def moderate(self, dialogue_str: str, obj_to_reply=None) -> str:
		"""
		Moderates a dialogue of comments.
		Optionally, a comment object can be passed in to reply to.
		"""

		needs_mod, toxicity, behav_type = self.moderation_classifier.measure_toxicity(dialogue_str)
		self.logger.debug(
			f'Toxicity score for "{dialogue_str}" = {toxicity} with behavior type = {behav_type}.')
		moderation_strategy = self.determine_moderation_strategy(dialogue_str)

		if needs_mod and moderation_strategy == 'respond' and obj_to_reply:

			author_username = get_username(obj_to_reply)

			init_reply = ""

			if author_username not in self.toxic_users:

				self.toxic_users.add(author_username)
				self.logger.debug(f'New Toxic Author name ----> {author_username}')

				initial_response = f"Hi, {author_username}, I'm a bot (check out my profile for details including how to get me to " \
				                   f"stop responding to you or collecting your comments)."

				self.logger.info(f'Initial Bot response generated: {initial_response}')
				translated_intial = self.translator.fran_translator(initial_response)

				if not self.test and translated_intial:
					self.logger.info(f'Sending out translated initial response to toxic user: {translated_intial}')
					# obj_to_reply.reply(translated_intial)
					init_reply = translated_intial

			parent = get_replied_to(obj_to_reply)

			best_response = f"It looks like you're {behav_type}{parent}. " + self.response_generator.get_random_comtype_resp()
			self.logger.info(f'Final response to toxic user: {best_response}')
			final_response = self.translator.fran_translator(best_response)

			final_response = init_reply + " " + final_response

			self.logger.info(f"Generated (and translated) final response: {final_response}\n")

		else:
			final_response = ""
			self.logger.info(
				f"NO RESPONSE generated based on moderation strategy: {moderation_strategy}. Toxicity Score = {toxicity} & with no Behav_type -> {len(behav_type)}\n")

		if not self.test and final_response and obj_to_reply:
			obj_to_reply.reply(final_response)

		return final_response
