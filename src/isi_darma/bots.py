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
		# TODO: Not working, still replies to everything
		if all([get_username(comment) != self.CREDS["username"] for comment in comment_queue]):
			self.moderate_post(submission)

		# dialogues is a list of comment objects
		dialogues = format_dialogue(comment_queue)
		for d in dialogues:
			last_comment = d[-1]
			username = get_username(last_comment.author)
			if username == self.CREDS["username"]:
				continue
			self.moderate_comment_thread(d, title=title, post_body=post_body)

	def moderate_post(self, submission):
		"""
		Process post before sending to moderate function
		"""
		title = submission.title
		post_body = submission.selftext
		authorname = submission.comments[0].author.name
		self.logger.debug('Author name ----> ', authorname)

		first_turn = f"{title} {post_body}".strip()
		translated_dialogue = [self.translator.rtg(first_turn)]
		self.moderate(translated_dialogue, submission, authorname)

	def moderate_comment_thread(self, dialogue, title="", post_body=""):
		"""
		Process comment thread before sending to moderate function
		"""
		self.current_dialogue = dialogue

		last_comment = dialogue[-1]
		author_username = get_username(last_comment.author)
		self.logger.debug(f'Author username for toxic comments: {author_username}')
		dialogue_text = get_dialogue_text(dialogue)
		self.logger.info(f"Retrieved dialogue: {dialogue_text}")

		source_language = self.detect_language(last_comment.body)
		self.logger.info(f"Translating all turns in dialogue")
		translated_dialogue = [self.translator.rtg(comment.body) for comment in dialogue]

		if title or post_body:
			first_turn = f"{title} {post_body}".strip()
			translated_dialogue = [self.translator.rtg(first_turn)] + translated_dialogue

		self.logger.info(f"Received Translated dialogue: {translated_dialogue}")
		self.moderate(translated_dialogue, last_comment, author_username=author_username)

	def moderate(self, dialogue_str: List[str], obj_to_reply=None, author_username=None) -> str:

		toxicity = self.moderation_classifier.measure_toxicity(dialogue_str[-1])
		needs_mod = self.moderation_classifier.needs_moderation(toxicity=toxicity)

		moderation_strategy = self.determine_moderation_strategy(dialogue_str[-1])

		# if moderation_strategy == "respond":
		# 	best_response = self.response_generator.generate_response(dialogue_str)
		# 	# 5: translate back to source language
		# 	self.logger.info(f"Sending best response for translation: {best_response}")
		# 	final_response = self.translator.fran_translator(best_response)
		#
		# 	response_toxicity = self.moderation_classifier.measure_toxicity(final_response)
		# 	response_needs_mod = self.moderation_classifier.needs_moderation(toxicity=response_toxicity)
		# 	if response_needs_mod:
		# 		# final_response = f"I know this is toxic, in fact {response_toxicity:.2f} toxic, but I'm going to say it: {final_response}"
		# 		final_response = f"Hi, {username}, I’m a bot (check out my profile for details) and it looks like you’re Toxic.\n"
		#
		# 	if needs_mod:
		# 		final_response = final_response + get_random_comtype_resp()
		# 		# final_response = f"Hey, that's toxic! In fact {toxicity * 100:.2f} toxic. \n {final_response}"
		# 	self.logger.info(f"Generated response: {final_response}")

		if needs_mod and moderation_strategy == 'respond':
			if author_username:
				initial_response = "Hi, I’m a bot (check out my profile for details) and it looks like you’re Toxic."
			else:
				initial_response = f"Hi {author_username}, I’m a bot (check out my profile for details) and it looks like you’re Toxic."

			if not self.test and initial_response and obj_to_reply:
				self.logger.info(f'Sending out initial response in response to toxic user: {initial_response}')
				obj_to_reply.reply(initial_response)

			best_response = self.response_generator.get_random_comtype_resp()
			self.logger.info(f'Randomly sampled Comtype response: {best_response}')
			final_response = self.translator.fran_translator(best_response)
			self.logger.info(f"Generated (and translated) response: {final_response}")

		else:
			final_response = ""
			self.logger.info(f"No response generated based on moderation strategy: {moderation_strategy}")

		if not self.test and final_response and obj_to_reply:
			obj_to_reply.reply(final_response)

		return final_response
