# imports
import random
import time
import openai
from boteval import log 


# define a retry decorator
def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = -1,
    errors: tuple = (openai.error.RateLimitError,),
):
    """Retry a function with exponential backoff.
    
    Ex.
        @retry_with_exponential_backoff
        def completions_with_backoff(**kwargs):
            return openai.Completion.create(**kwargs)
            
        completions_with_backoff(model="text-davinci-002", prompt="Once upon a time,")
    """

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            except errors as e:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                log.warning(f'OpenAI RateLimitError - sleeping for {delay} then retrying..')
                time.sleep(delay)

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper