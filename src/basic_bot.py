from loguru import logger 
from utils import load_credentials, load_reddit_client, get_username
from pipeline.response_generators import SpolinBotRG

SUBREDDIT="darma_test"
CREDS = load_credentials()

def needs_moderation(comment_str:str):
    """
    Skeleton code for moderation classification  
    Expand to take in more parameters (post, subreddit guidelines, etc.)
    """     
    return bool(comment_str)

def determine_moderation_strategy(comment_str:str, moderation_decision_result:str=None): 
    """
    Skeleton code for determining specific moderation strategy 
    """
    return "respond"

def detect_language(comment_str:str): 
    """
    Skeleton code for language detection 
    """

    return "english"

def translate(comment_str:str, language: str="english"): 
    """
    Skeleton code for translating to target language 
    """
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

        # determine whether to moderate 
        if not needs_moderation(comment.body): 
            continue 

        moderation_strategy = determine_moderation_strategy(comment.body)

        if moderation_strategy=="respond": 
            source_language = detect_language(comment.body)
            translated_comment = translate(comment.body, language="english")
            best_response = response_generator.generate_response(translated_comment)
            final_response = translate(best_response, language=source_language)

        logger.info(f"Generated response: {final_response}")

        comment.reply(final_response)
        logger.info(f"Replied to comment in subreddit {comment.subreddit}")
    return 


if __name__ == "__main__": 
    main() 