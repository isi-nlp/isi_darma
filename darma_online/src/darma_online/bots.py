from abc import ABC, abstractmethod
from darma_online.comments_utils import format_dialogue
from darma_online.logging_setup import setup_logger
from darma_online.pipeline.moderation_classifiers import PerspectiveAPIModerator
from darma_online.pipeline.response_generators import SpolinBotRG
from darma_online.pipeline.translators import Translator
from darma_online.pipeline.databases_manager import DatabaseManager
from darma_online.utils import load_credentials, get_username, check_for_opt_out, get_post_id
from darma_online.utils import get_replied_to, create_json_thread

class ModerationBot(ABC):

    @abstractmethod
    def moderate(self):
        pass

    @abstractmethod
    def determine_moderation_strategy(self):
        pass


class BasicBot(ModerationBot):

    def __init__(self, reddit_client=None, test=False, passive=False, sub='darma_test') -> None:
        super().__init__()

        self.test = test  # whether to actually post things to reddit
        self.sub = sub

        # Setup logger based on the 'test' flag
        if not self.test:
            self.logger = setup_logger(f'app_{sub}', f'logs/app_{sub}.log', test=self.test)
        else:
            self.logger = setup_logger(f'test_{sub}', f'logs/test_{sub}.log', test=self.test)

        self.passive = passive # whether to moderate comments or not
        self.logger.info("\n\n\n -------- STARTING NEW INSTANCE -------- \n\n\n")
        self.reddit_client = reddit_client
        self.response_generator = SpolinBotRG(self.logger)
        self.translator = Translator(self.logger)
        self.moderation_classifier = PerspectiveAPIModerator(self.logger)
        self.CREDS = load_credentials(self.logger)
        self.current_dialogue = None

        self.databases = DatabaseManager(self.logger, root = '/isi_darma/isi_darma/darma_online/src/darma_online/data')
        self.bot_responses = self.response_generator.read_responses( path = '/isi_darma/isi_darma/darma_online/src/darma_online/data/response_templates/responses.json')

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

        title, post_body = submission.title, submission.selftext

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
            self.moderate_comment_thread(last_comment)


    def moderate_post(self, submission):
        """
        Process post before sending to moderate function
        """
        title = submission.title
        post_body = submission.selftext
        self.logger.info(f'Moderating the POST "{title}" now....')

        first_turn = f"{title} {post_body}".strip()
        translated_dialogue = self.translator.rtg(first_turn)

        botReply = self.moderate(translated_dialogue, submission, type="post")
        if botReply: create_json_thread(self.logger, submission, True, botReply, subreddit=self.sub)
        else: self.logger.debug(f"No reply generated by Bot. Skipping JSON dump.\n\n")


    def moderate_comment_thread(self, dialogue):
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

            # source_language = self.detect_language(last_comment.body)
            self.logger.debug(f"Translating all turns in dialogue")
            translated_dialogue = self.translator.rtg(last_comment.body)

            # if title or post_body:
            # 	first_turn = f"{title} {post_body}".strip()
            # 	translated_dialogue = [self.translator.rtg(first_turn)] + translated_dialogue

            botReply = self.moderate(translated_dialogue, last_comment)
            if botReply: create_json_thread(self.logger, last_comment, False, botReply, subreddit=self.sub)
            else: self.logger.debug(f"No reply generated by Bot. Skipping JSON dump.\n\n")

        else:
            self.logger.debug(f'Not moderating self-comment with username: {get_username(last_comment)}\n\n')


    def moderate(self, dialogue_str: str, obj_to_reply=None, type="comment") -> str:
        """
        Moderates a dialogue from comments or posts
        Optionally, a reddit object can be passed in to reply to.
        """

        needs_mod, toxicity, behav_type = self.moderation_classifier.measure_toxicity(dialogue_str)
        self.logger.debug(f'Toxicity score for "{dialogue_str}" = {toxicity} with behavior type = {behav_type}')
        moderation_strategy = self.determine_moderation_strategy(dialogue_str)
        author_username = get_username(obj_to_reply) if obj_to_reply else "test_author"

        # Do not worry about users opt-ing out of moderation when in passive mode
        if not self.passive:
            opt_out = check_for_opt_out(dialogue_str)
            no_mod_user = self.databases.search_optout_db(author_username)
        else:
            opt_out, no_mod_user = False, False

        # Extract post id from object and check if already in database
        if type == 'post': post_id = get_post_id(obj_to_reply)
        else: post_id = get_post_id(obj_to_reply.submission)
        already_moderated = self.databases.search_moderated(post_id)

        # Check if user has opted out of moderation now or earlier
        if not already_moderated and not opt_out and not no_mod_user:

            # Check if user's dialogue needs moderation
            if needs_mod and moderation_strategy == 'respond' :

                self.logger.info(f'******** Toxic user {author_username} found. Responding to {type} ********')
                behav_type_response = self.bot_responses[f'{behav_type}_resp_fr']
                initial_response = f"Bonjour {author_username}, \n{self.bot_responses['init_resp_fr']} {behav_type_response}"
                self.logger.info(f'Initial response generated & translated with behav type based response = {behav_type_response}')

                if type == "post": parent_username = "les autres"
                else: parent_username = get_replied_to(obj_to_reply) if obj_to_reply else "other_test_user"

                # Change parent username to "others" if it's a self-reply
                if parent_username == author_username: parent_username = "les autres"

                # Response sampled from templates
                best_resp_template = self.response_generator.get_random_comtype_resp([parent_username])
                template_id, best_response = best_resp_template[0], best_resp_template[1]
                self.logger.info(f'Author username: {author_username} and parent username: {parent_username}')
                self.logger.info(f'Templated response selected for toxic user: {template_id} - {best_response}')

                # Combine initial and best response for FINAL response
                final_response = initial_response + '\n' + best_response
                self.logger.info(f"Generated (and translated) response.\n\n")
                if self.test: self.logger.debug(f"Final response: \n{final_response}\n")

            # Dialogue requires no moderation
            else:
                self.logger.info(
                    f"NO RESPONSE generated based on moderation strategy: {moderation_strategy}. Toxicity Score = {toxicity} & with no Behav_type -> {len(behav_type)}")
                final_response = ""

        # User has previously opted out of moderation
        elif no_mod_user:
            self.logger.info(f'User {author_username} in opt-out list. No moderation to be done.')
            final_response = ""

        # User opted-out of moderation, add to database
        elif opt_out:
            self.logger.info(f'{author_username} opted out of toxicity moderation, skipping moderation')
            self.databases.add_optout_user(author_username, dialogue_str)
            opt_out_response = f"D'accord, {author_username}, {self.bot_responses['opt_out_complete_fr']}"
            obj_to_reply.reply(opt_out_response)
            self.logger.info(f'Opt-out complete message sent to new user: {author_username} with message: {opt_out_response}')
            final_response = ""

        else:
            self.logger.info(f'Already moderated this post/comment with id {post_id} for {author_username}. Skipping moderation.\n\n')
            final_response = ""

        # Final response sent as reply in reddit thread/post
        if (not self.test and not self.passive) and final_response and obj_to_reply:
            obj_to_reply.reply(final_response)
            self.databases.add_to_moderated(post_id, author_username, dialogue_str)
            self.logger.info(f'Response sent to toxic user: {author_username}\n')

        else:
            self.logger.info(f'No Response sent. Test flag = {self.test}, passive flag = {self.passive}')
            self.logger.debug(f'Flags: already_moderated = {already_moderated}, opt_out = {opt_out}, no_mod_user = {no_mod_user}')
            self.logger.debug(f'Final response: {final_response if final_response else "<empty>"}')

        return final_response