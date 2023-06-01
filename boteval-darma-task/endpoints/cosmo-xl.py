import os
import re
import openai
import requests
from boteval import log 
from typing import Union, List, Dict
from . import Endpoint


class Cosmo_xl(Endpoint):

    name = 'cosmo-xl'
    
    def __init__(self):
        self.aws_ec2_dns = "http://ec2-44-199-199-221.compute-1.amazonaws.com:7860/generate"
        
        
    def query(self, 
              instruction: str, 
              turns:List[Dict],
              turn_idx: int,
              **kwargs):
        
        formatted_input = self._input_compose(instruction, turns, turn_idx, **kwargs)
        
        return self.query_completion_api(
            input_dict=formatted_input,
            **kwargs
        )
        

    def format_turn_text(self, turn): 
        try: 
            speaker_id = turn['data']['speaker_id']
        except Exception as e: 
            log.error(e)
            log.error(f"Did not find ['data']['speaker_id'] field in turn: {turn}")
            return turn['text']
            
        # if text starts with turn['speaker_id'], remove.
        if re.match(rf"^{speaker_id}: ", turn['text']): 
            log.debug(f"`{speaker_id}` in the beginning of turn text: `{turn['text']}`. Removing it.")
            turn_text = re.sub(rf"^{speaker_id}: ", '', turn['text'])
        else: 
            turn_text = turn['text']
        return turn_text


    def _input_compose(self, instruction:str, turns: List[Dict], turn_idx:int, **kwargs): 
        """
        input format for cosmo-xl endpoint. this can be easily parsed back to regular text for other plaintext endpoints
        """
        
        if kwargs.get('few_shot_example') == 'nvc':
            log.debug("cosmo-xl does not support few-shot example.")
        
        seed_turns =[turn for turn in turns if turn['is_seed']]
        non_seed_turns = [turn for turn in turns if not turn['is_seed']]

        conversation_history = []
        if seed_turns:
            conversation_history = [self.format_turn_text(turn) for turn in seed_turns]
        
        for t in non_seed_turns: 
            conversation_history.append(self.format_turn_text(t))       

        input_dict = {
            "situation": "",
            "instruction": "" if kwargs.get("exclude_topic") else str(instruction),
            "conversation": conversation_history,
        }

        return input_dict

    
    # @staticmethod
    def query_completion_api(
            self,
            input_dict: List[Dict[str,str]],
            top_p=1,
            temperature=0.7, 
            n=1,
            **kwargs,
        ):
        max_timeout_rounds = 5
        for _ in range(max_timeout_rounds):        
            
            log.debug(f"Input dictionary: {input_dict}")
            
            input_dict["temperature"] = temperature
            input_dict["top_p"] = top_p
            input_dict["num_return_sequences"] = n

            log.debug(f"Input dict: {input_dict}")
            res = requests.get(self.aws_ec2_dns, json=input_dict)
            
            response_text = res.json()['responses'][0].strip() 
            
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