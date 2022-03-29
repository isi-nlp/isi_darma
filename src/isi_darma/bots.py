from abc import ABC, abstractmethod
from typing import List

from isi_darma.comments_utils import format_dialogue, get_dialogue_text
from isi_darma.logging_setup import setup_logger
from isi_darma.pipeline.moderation_classifiers import PerspectiveAPIModerator
from isi_darma.pipeline.response_generators import SpolinBotRG
from isi_darma.pipeline.translators import Translator
from isi_darma.utils import load_credentials, get_username


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
			self.moderate_comment_thread(d, title=title, post_body=post_body)

	def moderate_post(self, submission):
		"""
		Process post before sending to moderate function
		"""
		title = submission.title
		post_body = submission.selftext
		self.logger.info(f'Moderating a POST "{title}" now....')

		first_turn = f"{title} {post_body}".strip()
		translated_dialogue = [self.translator.rtg(first_turn)]
		self.moderate(translated_dialogue, submission)

	def moderate_comment_thread(self, dialogue, title="", post_body=""):
		"""
		Process comment thread before sending to moderate function
		"""
		self.logger.info(f'Moderating a COMMENT THREAD now....')

		self.current_dialogue = dialogue
		last_comment = dialogue[-1]

		dialogue_text = get_dialogue_text(dialogue)
		self.logger.debug(f"Retrieved dialogue: {dialogue_text}")

		source_language = self.detect_language(last_comment.body)
		self.logger.debug(f"Translating all turns in dialogue")
		translated_dialogue = [self.translator.rtg(comment.body) for comment in dialogue]

		if title or post_body:
			first_turn = f"{title} {post_body}".strip()
			translated_dialogue = [self.translator.rtg(first_turn)] + translated_dialogue

		self.logger.debug(f"Received Translated dialogue: {translated_dialogue}")
		self.moderate(translated_dialogue, last_comment)

	def moderate(self, dialogue_str: List[str], obj_to_reply=None) -> str:

		toxicity = self.moderation_classifier.measure_toxicity(dialogue_str[-1])
		needs_mod = self.moderation_classifier.needs_moderation(toxicity=toxicity)
		self.logger.debug(f'Toxicity score from Perspective for "{dialogue_str[-1]}" = {toxicity}. needs_mod = {needs_mod}.')
		moderation_strategy = self.determine_moderation_strategy(dialogue_str[-1])

		if needs_mod and moderation_strategy == 'respond':

			if obj_to_reply:
				author_username = obj_to_reply.author
				self.logger.debug(f'Toxic post Author name ----> {author_username}')
				initial_response = f"Hi {author_username}, I’m a bot (check out my profile for details) and it looks like you’re Toxic."
				self.logger.debug(f'Initial Bot response generated: {initial_response}')
				translated_intial = self.translator.fran_translator(initial_response)
				self.logger.debug(f'Sending out initial response in response to toxic user: {translated_intial}')

			if not self.test and translated_intial:
				obj_to_reply.reply(translated_intial)

			best_response = self.response_generator.get_random_comtype_resp()
			self.logger.debug(f'Randomly sampled Comtype response: {best_response}')
			final_response = self.translator.fran_translator(best_response)
			self.logger.debug(f"Generated (and translated) response: {final_response}")

		else:
			final_response = ""
			self.logger.debug(f"No response generated based on moderation strategy: {moderation_strategy} and needs_mod: {needs_mod}")

		if not self.test and final_response and obj_to_reply:
			obj_to_reply.reply(final_response)

		return final_response
