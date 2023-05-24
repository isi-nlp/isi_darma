import os
import openai
from boteval import log 
from typing import Union, List, Dict
from . import Endpoint
import re 

class ChatGPT(Endpoint):

    name = 'chatgpt'
    
    def __init__(self):
        self.default_engine = 'gpt-3.5-turbo'
        
        # Override option for backward compatability
        self.engine  = os.environ.get(
            'OPENAI_ENGINE', 
            self.default_engine
        )  
             
        api_key = os.environ.get('OPENAI_KEY', '')
        if not api_key:
            raise Exception("OpenAI API key is not set."
                            " Please 'export OPENAI_KEY=<key>' and rerun."
                            " You may obtain key from https://beta.openai.com/account/api-keys")            
        openai.api_key = api_key
        
        
    def query(self, 
              instruction: str, 
              turns:List[Dict],
              turn_idx: int,
              **kwargs):
        
        formatted_messages = self._messages_compose(instruction, turns, turn_idx, **kwargs)
        
        return self.query_completion_api(
            messages= formatted_messages,  
            engine=self.engine,
            **kwargs
        )
        

    def format_turn_text(self, turn): 
        try: 
            speaker_id = turn['data']['speaker_id']
        except Exception as e: 
            log.error(e)
            log.error(f"Did not find ['data']['speaker_id'] field in turn: {turn}")
            return turn['text']
            
        # if text doesn't start with turn['user_id'], append: 
        if not re.match(rf"^{speaker_id}: ", turn['text']): 
            log.debug(f"`{speaker_id}` not in the beginning of turn text: `{turn['text']}`. Prepending it.")
            turn_text = f"{speaker_id}: {turn['text']}"
        else: 
            turn_text = turn['text']
        return turn_text

    def _messages_compose(self, instruction:str, turns: List[Dict], turn_idx:int, **kwargs): 
        """
        messages format for chatgpt endpoint (gpt-3.5-turbo). this can be easily parsed back to regular text for other plaintext endpoints
        """
        
        # if kwargs.get('leaf_variable', False):
        #     # TODO; add support for instruction after context; check gpt3 implementation            
            
        #     return [{
        #         "role": "system", "content": "\n".join([instruction] + [t[0] for t in turns]).strip()
        #     }]
        
        # else; root variable
        
        if kwargs.get('few_shot_example') == 'nvc':
            few_shot_example = self.get_fewshot_example(turn_idx)
            if few_shot_example != "":
                instruction = f'{instruction}\n{few_shot_example}\n'
        
        seed_turns =[turn for turn in turns if turn['is_seed']]
        non_seed_turns = [turn for turn in turns if not turn['is_seed']]
                
        
        if kwargs.get("exclude_topic"):
            messages = []
        else:
            messages = [
                {"role": "system", "content": str(instruction)}, 
            ]
        
        if seed_turns:
            seed_turn_texts = [self.format_turn_text(turn) for turn in seed_turns]
            
            messages.append(
                {"role": "user", "content": "\n".join(seed_turn_texts).strip()}
            )
        
        for t in non_seed_turns: 
            # TODO hardcoded values.. need to be changed
            if t['user_id'] != "Moderator": 
                role = "user"
            else: 
                role = "assistant"
                
            role_override = kwargs.get('role')
            if role_override is not None:
                role = role_override
                
            messages.append({
                "role": role, 
                "content": self.format_turn_text(t)
            })
                    
        return messages
    
    @staticmethod
    def query_completion_api(
            messages: List[Dict[str,str]], engine:str,
            frequency_penalty=0, presence_penalty=0,
            temperature=0.7, n=1,
            **kwargs
        ):
        log.debug(f"Using engine: {engine}")
        max_timeout_rounds = 5
        for _ in range(max_timeout_rounds):        
            
            log.debug(f"Input messages: {messages}")
            
            
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
            
            log.debug(f"Output response: {response_text}")
                        

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
    
class GPT4(ChatGPT):
    name = "gpt4"
    
    def __init__(self):
        super().__init__()
        self.default_engine = 'gpt-4'
        self.engine = os.environ.get(
            'OPENAI_ENGINE', 
            self.default_engine
        )