from requests import post
from loguru import logger
from utils import load_credentials, load_reddit_client, get_username
from pipeline.response_generators import SpolinBotRG

SUBREDDIT = "darma_test"
# Assuming (for MVP) that the RTG MT will run on the same machine as this project.
RTG_API = 'http://localhost:6060/translate'
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

    source = {'source': [comment_str]}
    response = post(RTG_API, json=source)
    if response.ok:
        response = response.json()
        logger.info(f'Received translation from RTG for {response.source} -> {response.translation}')
        return response.translation[0]
    else:
        logger.warning(f'Translation failed with {response.status_code} -> {response.reason}!')
        logger.warning(f'Response Body from RTG:\n{response.json()}')
        return comment_str


def main():
    reddit_client = load_reddit_client()
    logger.info("Instantiated Reddit Client")

    # get replies 
    subreddit = reddit_client.subreddit(SUBREDDIT)

    # instantiate response generator
    response_generator = SpolinBotRG()

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
        if source_language != "english":
            translated_comment = translate(comment.body, language=source_language)
        else:
            translated_comment = comment.body

        # 2: determine if moderation is needed 
        if not needs_moderation(comment.body):
            continue

            # 3: determine the moderation strategy
        moderation_strategy = determine_moderation_strategy(translated_comment)

        if moderation_strategy == "respond":
            # 4: generate a response
            best_response = response_generator.generate_response(translated_comment)
            # 5: translate back to source language
            final_response = translate(best_response, language=source_language)

        # TODO: Need to add code for when bot the decides NOT to respond
        logger.info(f"Generated response: {final_response}")

        comment.reply(final_response)
        logger.info(f"Replied to comment in subreddit {comment.subreddit}")
    return


if __name__ == "__main__":
    main()
