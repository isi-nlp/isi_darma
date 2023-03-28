import os
import openai
from boteval import log
from typing import List
from . import Endpoint

class GPT3(Endpoint):

    name = 'gpt3'
    
    def __init__(self):
        self.default_engine = 'text-davinci-003'
        
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
              turns:List[tuple],
              turn_idx: int,
              **kwargs):
        
        return self.query_completion_api(
            self._prompt_compose(instruction, turns, turn_idx, **kwargs), 
            engine=self.engine,
            **kwargs
        )
        
            
    def _prompt_compose(self, instruction, turns, turn_idx, **kwargs) -> str:
        """
        Returns:
            str: Prepared and generated/constant prompt appended to turns properly to feed for completion llm call.
        """        
        def prepare_context(turns: List[tuple]):
            # seed_turns = [x[0] for x in turns if x[-1]]
            # non_seed_turns = [x[0] for x in turns if not x[-1]]
            all_turns = [t[0] for t in turns]
            _look_up = kwargs.get('look_up')
            if not _look_up:
                return '\n'.join(all_turns)
            if _look_up > 0:
                return '\n'.join(all_turns[:_look_up])
            else:
                return '\n'.join(all_turns[_look_up:])
         
        _few_shot_example = kwargs.get('few_shot_example')
        
        context = prepare_context(turns)

        if kwargs.get('leaf_variable', False):    
            if kwargs.get('instruction_first', False):
                return "\n".join([instruction, context])
            else:
                return "\n".join([context, instruction])
        else: 
            # root variable; instruction leading the conversation
            if _few_shot_example == 'nvc':
                few_shot_example = self.get_fewshot_example(turn_idx)
                prompt = f'{instruction}\n\n{few_shot_example}\n\n' +\
                    f'###\n\n{context}\n'
            else:
                prompt = f'{instruction}\n\n{context}\n'

            return prompt + f'user {kwargs.get("persona_title")}:'
            
    
    @staticmethod
    def query_completion_api(
            prompt, engine,
            frequency_penalty=0, 
            presence_penalty=0,
            temperature=0.7,
            n=1,
            max_timeout_rounds = 5,
            **kwargs
        ):
        
        for i in range(max_timeout_rounds):
            # GPT-3 Generation
            if i > 0:
                log.critical(f'GPT timeout - retry #{i}')
                
            log.debug(f"Input prompt: {prompt}")
                
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
            
            # Toxicity Classification
            # https://beta.openai.com/docs/models/content-filter
            # 0: safe, 1: sensitive, 2: unsafe
            # We want to make sure the generation is not unsafe
            response_text = response.choices[0].text.strip()
            
            log.debug(f"Output response: {response_text}")
            
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