from abc import ABC, abstractmethod
from darma_online.comments_utils import format_dialogue
from darma_online.logging_setup import setup_logger
from darma_online.pipeline.moderation_classifiers import PerspectiveAPIModerator
from darma_online.pipeline.response_generators import SpolinBotRG
from darma_online.pipeline.translators import Translator
from darma_online.pipeline.databases_manager import DatabaseManager
from darma_online.utils import load_credentials, load_config, get_username, check_for_opt_out, get_post_id
from darma_online.utils import get_replied_to, create_json_thread
from prawcore.exceptions import Forbidden

class ModerationBot(ABC):

    @abstractmethod
    def moderate(self):
        pass

    @abstractmethod
    def determine_moderation_strategy(self):
        pass


class BasicBot(ModerationBot):

    def __init__(self,
                 reddit_client=None,
                 test=False,
                 passive=False,
                 sub_name='darma_test',
                 sub_obj=None,
                 lang='french',
                 mod_assist=False,
                 logger=None) -> None:
        super().__init__()

        self.test = test  # whether to actually post things to reddit
        self.sub_name = sub_name
        self.sub_obj = sub_obj if sub_obj else reddit_client.subreddit(sub_name)
        self.moderators = None
        self.mod_assist = mod_assist
        self.language = lang

        self.logger = logger if logger else setup_logger(f'bot_{sub_name}', f'logs/BasicBot_{sub_name}.log', test=test)

        self.CREDS = load_credentials(self.logger)
        self.CONFIG = load_config(self.logger)

        self.passive = passive # whether to moderate comments or not
        self.logger.info("\n\n\n -------- STARTING NEW INSTANCE -------- \n\n\n")
        self.reddit_client = reddit_client
        self.response_generator = SpolinBotRG(self.logger)
        self.translator = Translator(self.logger)
        self.moderation_classifier = PerspectiveAPIModerator(self.logger, config=self.CONFIG)
        self.current_dialogue = None

        self.databases = DatabaseManager(self.logger, root = self.CONFIG["data_path"])
        self.bot_responses = self.response_generator.read_responses( path = self.CONFIG["bot_responses"] )[lang]

    @staticmethod
    def detect_language(text):
        return "english"


    def translate(self, text):
        if self.language == 'eng' or self.language == 'english':
            return text

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
        translated_dialogue = self.translate(first_turn)

        botReply = self.moderate(first_turn, translated_dialogue, submission, type="post")
        if botReply: create_json_thread(self.logger, submission, True, botReply, subreddit=self.sub_name)
        else: self.logger.debug("No reply generated by Bot. Skipping JSON dump.\n\n")


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
            self.logger.debug("Translating all turns in dialogue")
            translated_dialogue = self.translate(last_comment.body)

            # if title or post_body:
            # 	first_turn = f"{title} {post_body}".strip()
            # 	translated_dialogue = [self.translator.rtg(first_turn)] + translated_dialogue

            botReply = self.moderate(last_comment.body, translated_dialogue, last_comment)
            if botReply: create_json_thread(self.logger, last_comment, False, botReply, subreddit=self.sub_name, json_output_path=self.CONFIG["json_output_path"])
            else: self.logger.debug("No reply generated by Bot. Skipping JSON dump.\n\n")

        else:
            self.logger.debug(f'Not moderating self-comment with username: {get_username(last_comment)}\n\n')


    def moderate(self, original_dialogue:str, dialogue_str: str, obj_to_reply=None, type="comment") -> str:
        #TODO: Break into smaller methods
        """
        Moderates a dialogue from comments or posts
        Optionally, a reddit object can be passed in to reply to.
        """

        needs_mod, tox_score, behav_score, behav_type = self.moderation_classifier.measure_toxicity(dialogue_str)
        self.logger.debug(f'Toxicity score for "{dialogue_str}" = {tox_score} with behavior type = {behav_type}')
        moderation_strategy = self.determine_moderation_strategy(dialogue_str)
        toxic_user = get_username(obj_to_reply) if obj_to_reply else "test_author"

        # Do not worry about users opt-ing out of moderation when in passive mode
        if not self.passive:
            opt_out = check_for_opt_out(dialogue_str)
            no_mod_user = self.databases.search_optout_db(toxic_user)
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

                self.logger.info(f'******** Toxic user {toxic_user} found. Responding to {type} ********')
                behav_type_response = self.bot_responses[f'{behav_type}_resp']
                initial_response = f"Bonjour {toxic_user}, \n{self.bot_responses['init_resp']} {behav_type_response}"
                self.logger.info(f'Initial response generated & translated with behav type based response = {behav_type_response}')

                if type == "post": parent_username = "envers les autres"
                else: parent_username = get_replied_to(obj_to_reply) if obj_to_reply else "envers other_test_user"

                # Change parent username to "others" if it's a self-reply
                if parent_username == toxic_user: parent_username = "les autres"

                # Response sampled from templates
                best_response = self.response_generator.get_random_resp(self.bot_responses["responses"], [parent_username])
                self.logger.info(f'Author username: {toxic_user} and parent username: {parent_username}')
                self.logger.info(f'Templated response selected for toxic user: {best_response}')

                # Combine initial and best response for FINAL response
                final_response = initial_response + '\n' + best_response
                self.logger.info("Generated (and translated) response.\n\n")
                if self.test: self.logger.debug(f"Final response: \n{final_response}\n")

            # Dialogue requires no moderation
            else:
                self.logger.info(
                    f"NO RESPONSE generated based on moderation strategy: {moderation_strategy}. Toxicity Score = {tox_score} & with Behav_type -> {behav_type}")
                final_response = ""

        # User has previously opted out of moderation
        elif no_mod_user:
            self.logger.info(f'User {toxic_user} in opt-out list. No moderation to be done.')
            final_response = ""

        # User opted-out of moderation, add to database
        elif opt_out:
            self.logger.info(f'{toxic_user} opted out of toxicity moderation, skipping moderation')
            self.databases.add_optout_user(toxic_user, dialogue_str)
            opt_out_response = f"{self.bot_responses['hello']}, {toxic_user}, {self.bot_responses['opt_out_complete']}"
            obj_to_reply.reply(opt_out_response)
            self.logger.info(f'Opt-out complete message sent to new user: {toxic_user} with message: {opt_out_response}')
            final_response = ""

        else:
            self.logger.info(f'Already moderated this post/comment with id {post_id} for {toxic_user}. Skipping moderation.\n\n')
            final_response = ""

        # Final response sent as reply in reddit thread/post
        if (not self.test and not self.passive) and final_response and obj_to_reply:

            try:
                if not self.mod_assist:
                    obj_to_reply.reply(final_response)
                else:
                    url = obj_to_reply.submission.url
                    if self.language != 'english':
                        dialogue = original_dialogue
                    else:
                        dialogue = dialogue_str
                    self.msg_mods(toxic_user, tox_score, behav_type, parent_username, best_response, dialogue, url)
                self.databases.add_to_moderated(post_id, toxic_user, dialogue_str)
                self.logger.info(f'Response sent to toxic user: {toxic_user}\n')

            except Forbidden:
                self.logger.info(f"Cannot send response to toxic user on r/{self.sub_name} - Forbidden")
                return final_response

        else:
            self.logger.info(f'No Response sent. Test flag = {self.test}, passive flag = {self.passive}')
            self.logger.debug(f'Flags: already_moderated = {already_moderated}, opt_out = {opt_out}, no_mod_user = {no_mod_user}')
            self.logger.debug(f'Final response: {final_response if final_response else "<empty>"}')

        return final_response

    def msg_mods(self, toxic_user, tox_score, behav_type, parent_username, best_response, dialogue_str, url):
        """
        Sends a message to moderators with details of the toxic comment
        """

        message_body = f"##### {self.bot_responses['init_mod_msg']} \n" \
           f"- **Toxic user:** {toxic_user} \n" \
           f"- **Toxicity score:** {tox_score} \n" \
           f"- **Behavior type:** {behav_type} \n" \
           f"- **Victim username:** {parent_username} \n" \
           f"- **Toxic comment:** {dialogue_str} \n" \
           f"- **Link to comment:** {url} \n" \
           f"- **Possible response:** {best_response} \n\n"\
           f"{self.bot_responses['mod_action_request']}{toxic_user}".format(**locals())

        self.logger.info(f"Sending following message to moderators with details about toxic comment: \n{message_body}")
        self.sub_obj.message(message = message_body, subject = "Toxic comment detected | DARMA Bot")
