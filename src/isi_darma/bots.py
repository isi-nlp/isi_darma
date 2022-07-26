from abc import ABC, abstractmethod

from isi_darma.comments_utils import format_dialogue
from isi_darma.logging_setup import setup_logger
from isi_darma.pipeline.moderation_classifiers import PerspectiveAPIModerator
from isi_darma.pipeline.response_generators import SpolinBotRG
from isi_darma.pipeline.translators import Translator
from isi_darma.utils import load_credentials, get_username, check_for_opt_out, add_to_db, read_db, user_in_db, read_responses


class ModerationBot(ABC):

	@abstractmethod
	def moderate(self):
		pass

	@abstractmethod
	def determine_moderation_strategy(self):
		pass


class BasicBot(ModerationBot):

	def __init__(self, reddit_client=None, test=False, db = '') -> None:
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
		self.db = read_db(db)
		self.bot_info_fr = read_responses()["bot_info_fr"]

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
		self.moderate(translated_dialogue, submission)

	def moderate_comment_thread(self, dialogue):
		"""
		Process comment thread before sending to moderate function
		"""
		last_comment = dialogue

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
			self.moderate(translated_dialogue, last_comment)

		else:
			self.logger.debug(f'Self comment -> {last_comment.body} with username: {get_username(last_comment)}')

	def moderate(self, dialogue_str: str, obj_to_reply=None) -> str:
		"""
		Moderates a dialogue of comments.
		Optionally, a comment object can be passed in to reply to.

		If statements hierarchy:
		- Opt-out
		- Needs moderation and moderation stategy
		- If test flag is set
		- If obj_to_reply is exists
		"""

		needs_mod, toxicity, behav_type = self.moderation_classifier.measure_toxicity(dialogue_str)
		self.logger.debug(f'Toxicity score for "{dialogue_str}" = {toxicity} with behavior type = {behav_type}.')
		moderation_strategy = self.determine_moderation_strategy(dialogue_str)

		opt_out = check_for_opt_out(dialogue_str)

		#TODO: Consolidate if statements in this method for cleaner control flow
		if not opt_out and not user_in_db(get_username(obj_to_reply), self.db):

			if needs_mod and moderation_strategy == 'respond' and ( obj_to_reply or self.test) :

				author_username = get_username(obj_to_reply)

				# TODO: Respond only once per user i.e. remove the toxic users store
				initial_response = f"Bonjour, {author_username}, Je suis un bot informatique (consultez mon profil pour plus de détails, " \
				                   f"notamment pour savoir comment faire pour que je cesse de vous répondre ou de recueillir vos commentaires) et vous semblez "
				self.logger.info(f'Initial response generated & translated.')

				# Response sampled from templates
				# TODO: Replace english with translated french responses to templates
				best_response = self.response_generator.get_random_comtype_resp()
				self.logger.info(f'Final response to toxic user: {best_response}')

				# Combine initial and best response for FINAL response
				final_response = initial_response + ' ' + best_response
				self.logger.info(f"Generated (and translated) final response: {final_response}\n")
				final_response += '\n' + self.bot_info_fr
				self.logger.info(f"Added bot info to final response.")

			# No response sent to user
			else:
				final_response = ""
				self.logger.info(
					f"NO RESPONSE generated based on moderation strategy: {moderation_strategy}. Toxicity Score = {toxicity} & with no Behav_type -> {len(behav_type)}\n")

		# User opted-out of moderation in comments, add to database and no moderation/response
		else:
			author_username = get_username(obj_to_reply)
			self.logger.info(f'{author_username} opted out of toxicity moderation, skipping moderation')
			self.db = add_to_db(self.db, author_username, toxicity, behav_type)
			final_response = ""

		# Final response sent as reply in reddit thread/post
		if not self.test and final_response and obj_to_reply:
			obj_to_reply.reply(final_response)
			self.logger.info(f'Response sent to toxic user: {get_username(obj_to_reply)}')
