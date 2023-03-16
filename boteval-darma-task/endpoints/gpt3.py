import os
import openai
from typing import Union, List, Dict
from . import Endpoint
from boteval import log

@Endpoint.register
class GPT3:

    name = 'gpt3'
    
    def __init__(self):
    
        api_key = os.environ.get('OPENAI_KEY', '')
        if not api_key:
            raise Exception("OpenAI API key is not set."
                            " Please 'export OPENAI_KEY=<key>' and rerun."
                            " You may obtain key from https://beta.openai.com/account/api-keys")            
        openai.api_key = api_key
    
    def query(self, messages, engine: str, **args):

        return self.query_completion_api(
            messages=messages,  
            engine=engine,
            **args
        )
    
    @staticmethod
    def query_completion_api(
            messages: List[Dict[str,str]], engine:str,
            frequency_penalty=0, presence_penalty=0,
            temperature=0.7, n=1
        ):
        max_timeout_rounds = 5
        for _ in range(max_timeout_rounds):
            # GPT-3 Generation
            
            if "text" in engine:
                
                prompt = "\n".join([msg["content"] for msg in messages]) + "\n"
                
                response = openai.Completion.create(
                    model=engine,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=1024,
                    top_p=1,
                    n=n,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stop=["user A:", "user B:", "user C:", "user D:"]
                )
                
                response_text = response.choices[0].text.strip()
                
            else: 
                response = openai.ChatCompletion.create(
                    model=engine,
                    messages = messages, 
                    temperature=temperature,
                    max_tokens=1024,
                    top_p=1,
                    n=n,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stop=["user A:", "user B:", "user C:", "user D:"]
                )
                
                response_text = response.choices[0]['message']['content'].strip() 

            # Toxicity Classification
            # https://beta.openai.com/docs/models/content-filter
            # 0: safe, 1: sensitive, 2: unsafe
            # We want to make sure the generation is not unsafe
            classification_response = openai.Completion.create(
                model="content-filter-alpha",
                prompt = "<|endoftext|>"+ response_text +"\n--\nLabel:",
                temperature=0,
                max_tokens=1,
                top_p=0,
                logprobs=10
            )
            output_label = classification_response["choices"][0]["text"]
            # This is the probability at which we evaluate that a "2" is likely real
            # vs. should be discarded as a false positive
            toxic_threshold = -0.355


            # If the filter returns 0 or 1, you should accept that as the filter's outcome. 
            # If the filter returns 2, you should accept this outcome only if its logprob is greater than -0.355.
            # If the logprob for 2 is beneath -0.355 (for example, -0.4), 
            # then you should use as output whichever of 0 or 1 has a logprob closer to 0.
            if output_label == "2":
                # If the model returns "2", return its confidence in 2 or other output-labels
                logprobs = classification_response["choices"][0]["logprobs"]["top_logprobs"][0]

                # If the model is not sufficiently confident in "2",
                # choose the most probable of "0" or "1"
                # Guaranteed to have a confidence for 2 since this was the selected token.
                if logprobs["2"] < toxic_threshold:
                    logprob_0 = logprobs.get("0", None)
                    logprob_1 = logprobs.get("1", None)

                    # If both "0" and "1" have probabilities, set the output label
                    # to whichever is most probable
                    if logprob_0 is not None and logprob_1 is not None:
                        if logprob_0 >= logprob_1:
                            output_label = "0"
                        else:
                            output_label = "1"
                    # If only one of them is found, set output label to that one
                    elif logprob_0 is not None:
                        output_label = "0"
                    elif logprob_1 is not None:
                        output_label = "1"

                    # If neither "0" or "1" are available, stick with "2"
                    # by leaving output_label unchanged.

            # if the most probable token is none of "0", "1", or "2"
            # this should be set as unsafe
            if output_label not in ["0", "1", "2"]:
                output_label = "2"

            # only return the response if the response is not toxic
            if output_label != "2":
                return response_text

        # if timeout, then return something generic
        timeout_response = "I don't really know what to say about that."
        return timeout_response
