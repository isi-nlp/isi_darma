from abc import ABC, abstractmethod
from typing import List

from basic_bot import determine_moderation_strategy
from isi_darma.comments_utils import format_dialogue, get_dialogue_text
from isi_darma.logging_setup import setup_logger
from isi_darma.pipeline.moderation_classifiers import PerspectiveAPIModerator
from isi_darma.pipeline.response_generators import SpolinBotRG
from isi_darma.pipeline.translators import Translator
from isi_darma.utils import load_credentials, get_username


CREDS = load_credentials()


class ModerationBot(ABC):

	@abstractmethod
	def moderate(self):
		pass

	@abstractmethod
	def determine_moderation_strategy(self):
		pass


class BasicBot(ModerationBot):

	def __init__(self, reddit_client=None, response_generator=SpolinBotRG(), translator=Translator(), moderation_classifier=PerspectiveAPIModerator(), test=False) -> None:
		super().__init__()

		self.test = test  # whether to actually post things to reddit
		if not self.test:
			self.logger = setup_logger('app', '../logs/app.log', test=self.test)
		else:
			self.logger = setup_logger('test', 'logs/test.log', test=self.test)
		self.reddit_client = reddit_client
		self.response_generator = response_generator
		self.translator = translator
		self.moderation_classifier = moderation_classifier

	@staticmethod
	def detect_language(text):
		return "english"

	def translate(self, text):
		return self.translator.rtg(text)

	def determine_moderation_strategy(self):
		return "respond"

	def generate_response(self, dialogue):
		return self.response_generator.generate_response(dialogue)

	def moderate_submission(self, submission):

		title = submission.title
		post_body = submission.selftext

		submission.comments.replace_more(limit=None)
		comment_queue = submission.comments[:]  # Seed with top-level

		# check that we didn't already moderate the post
		if all([get_username(comment) != CREDS["username"] for comment in comment_queue]):
			self.moderate_post(submission)

		# dialogues is a list of comment objects
		dialogues = format_dialogue(comment_queue)
		for d in dialogues:
			last_comment = d[-1]
			username = get_username(last_comment.author)
			if username == CREDS["username"]:
				continue
			self.moderate_comment_thread(d, title=title, post_body=post_body)

	def moderate_post(self, submission):
		"""
		Process post before sending to moderate function
		"""
		title = submission.title
		post_body = submission.selftext

		first_turn = f"{title} {post_body}".strip()
		translated_dialogue = [self.translator.rtg(first_turn)]
		self.moderate(translated_dialogue, submission)

	def moderate_comment_thread(self, dialogue, title="", post_body=""):
		"""
		Process comment thread before sending to moderate function
		"""
		self.current_dialogue = dialogue

		last_comment = dialogue[-1]
		dialogue_text = get_dialogue_text(dialogue)
		self.logger.info(f"Retrieved dialogue: {dialogue_text}")

		source_language = self.detect_language(last_comment.body)
		self.logger.info(f"Translating all turns in dialogue")
		translated_dialogue = [self.translator.rtg(comment.body) for comment in dialogue]

		if title or post_body:
			first_turn = f"{title} {post_body}".strip()
			translated_dialogue = [self.translator.rtg(first_turn)] + translated_dialogue

		self.logger.info(f"Received Translated dialogue: {translated_dialogue}")
		self.moderate(translated_dialogue, last_comment)

	def moderate(self, dialogue_str: List[str], obj_to_reply=None) -> str:

		toxicity = self.moderation_classifier.measure_toxicity(dialogue_str[-1])
		needs_mod = self.moderation_classifier.needs_moderation(toxicity=toxicity)

		moderation_strategy = determine_moderation_strategy(dialogue_str[-1])

		if moderation_strategy == "respond":
			best_response = self.response_generator.generate_response(dialogue_str)
			# 5: translate back to source language
			self.logger.info(f"Sending best response for translation: {best_response}")
			final_response = self.translator.fran_translator(best_response)

			response_toxicity = self.moderation_classifier.measure_toxicity(final_response)
			response_needs_mod = self.moderation_classifier.needs_moderation(toxicity=response_toxicity)
			if response_needs_mod:
				final_response = f"I know this is toxic, in fact {response_toxicity:.2f} toxic, but I'm going to say it: {final_response}"

			if needs_mod:
				final_response = f"Hey, that's toxic! In fact {toxicity * 100:.2f} toxic. \n {final_response}"
			self.logger.info(f"Generated response: {final_response}")

		else:
			final_response = ""
			self.logger.info(f"No response generated based on moderation strategy: {moderation_strategy}")

		if not self.test and final_response and obj_to_reply:
			obj_to_reply.reply(final_response)
			self.logger.info(f"Replied to comment/post in subreddit {obj_to_reply.subreddit}")

		return final_response
