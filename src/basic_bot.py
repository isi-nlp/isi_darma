from logging_setup import logger
from utils import load_credentials, load_reddit_client, get_username
from pipeline.response_generators import SpolinBotRG
from pipeline.translators import Translator

logger.info("\n\n\n")
SUBREDDIT = "darma_test"
CREDS = load_credentials()


def needs_moderation(comment_str: str):
    """
    Skeleton code for moderation classification  
    Expand to take in more parameters (post, subreddit guidelines, etc.)
    """
    return bool(comment_str)


def determine_moderation_strategy(comment_str: str, moderation_decision_result: str = None):
    """
    Skeleton code for determining specific moderation strategy 
    """
    return "respond"


def detect_language(comment_str: str):
    """
    Skeleton code for language detection
    TODO: Check if RTG has an API to enable this.
    """

    return "english"


def translate(comment_str: str, language: str = "english"):
    """
    Skeleton code for translating to target language 
    """
    # Functionality moved to pipeline.translators
    pass


def main():
    reddit_client = load_reddit_client()
    logger.info("Instantiated Reddit Client")

    # get replies 
    subreddit = reddit_client.subreddit(SUBREDDIT)

    # instantiate response generator
    response_generator = SpolinBotRG()
    translator = Translator()

    for comment in subreddit.stream.comments():

        # don't reply to bot's own comments 
        # TODO: don't reply again to comments that the bot already replied to. 
        username = get_username(comment.author)
        if username == CREDS["username"]:
            continue

            # otherwise, respond
        logger.info(f"Retrieved non-bot comment: {comment.body}")

        # 1: translate
        source_language = detect_language(comment.body)
        logger.info(f"Sending comment body for translation: {comment.body}")
        translated_comment = translator.rtg(comment.body)
        logger.info(f"Received Translated Comment: {translated_comment}")

        # 2: determine if moderation is needed 
        if not needs_moderation(comment.body):
            continue

        # 3: determine the moderation strategy
        moderation_strategy = determine_moderation_strategy(translated_comment)

        if moderation_strategy == "respond":
            # 4: generate a response
            best_response = response_generator.generate_response(translated_comment)
            # 5: translate back to source language
            logger.info(f"Sending best response for translation: {best_response}")
            final_response = translator.fran_translator(best_response)

        # TODO:  Add logic for when bot the decides NOT to respond, final_response empty in that case
        logger.info(f"Generated response: {final_response}")

        comment.reply(final_response)
        logger.info(f"Replied to comment in subreddit {comment.subreddit}")
    return


if __name__ == "__main__":
    main()
