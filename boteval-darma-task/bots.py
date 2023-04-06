"""
This work is done by Taiwei Shi during his internship at USC ISI (Summer 2022).
"""

import os
import json

import endpoints
from prompt_generator import PromptGenerator
from boteval import log, C, registry as R
from boteval.model import ChatMessage
from boteval.bots import BotAgent
from typing import Dict, List, Union, Any

@R.register(R.BOT, name="gpt")
class GPTBot(BotAgent):

    def __init__(self, persona_id: str,
            *args, engine: str=None, api_key='',
            default_endpoint='gpt3',
            few_shot_example=None, max_ctx_len=2048,
            persona_configs_relative_filepath='persona_configs.json',
            num_threads=None,
            allow_endpoint_override=True,
            **kwargs):
        super().__init__(*args, name="gpt", **kwargs)
        
        self.max_ctx_len = max_ctx_len
        self.few_shot_example = few_shot_example # e.g. nvc
        self.default_endpoint = default_endpoint
        self.engine = engine 
        
        if engine:
            # TODO remove completely .. still used only for backward compatibility..
            # it would override the default engine across all valid endpoints!! (openai ones)
            # preferably create complete new endpoints if necessary to use different engine
            os.environ['OPENAI_ENGINE'] = engine
        
        if api_key:
            # Read by endpoint implementation
            os.environ['OPENAI_KEY'] = api_key

        self.setup_endpoints()
        
        self.prompt_generator = self.load_persona(
            persona_id,
            configs_relative_filepath=\
                persona_configs_relative_filepath,
            num_threads=num_threads,
            allow_endpoint_override=allow_endpoint_override
        )
        
        self.turn_idx = 0
        self.context = []
        
        log.info(
            f"Initialized GPT bot with {engine=}"
            f"{self.prompt_generator.id=}"
            f"{self.prompt_generator.title=}\n"
            f"{self.prompt_generator.instruction._instruction_raw=}")
        

    def setup_endpoints(self):
        self.endpoints = endpoints.endpoints_dict        
        endpoints_listing = "\n\t".join([
            f"- {k}" for k in self.endpoints.keys()
        ])
        log.info(
            f"\nAvailable endpoints:\n{endpoints_listing}\n"
            f"\twhile default is {self.default_endpoint}"
        )

    def load_persona(self, 
                     persona_id:str,
                     configs_relative_filepath='persona_configs.json',
                     num_threads=None,
                     allow_endpoint_override=False):
        
        configs_filepath =\
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                configs_relative_filepath
            )

        with open(configs_filepath, mode='r') as f:
            persona_jsons = json.load(f)
            matching_personas = [
                x
                for x in persona_jsons if x['id']==persona_id
            ]
            
            if len(matching_personas) < 1:
                raise Exception(f'Unknown persona: {persona_id}')
            elif len(matching_personas) > 1:
                log.warning(f'Redundant personas with id "{persona_id}" exist!')


            if allow_endpoint_override:
                self.default_endpoint =\
                    matching_personas[0].get('default_endpoint', self.default_endpoint)
                
            return PromptGenerator(
                matching_personas[0], 
                self.endpoints,
                # self.engine,
                default_endpoint=self.default_endpoint,
                few_shot_example=self.few_shot_example,
                num_threads=num_threads
            )
    
    def _get_turns(self) -> str:
        # truncate to not exceed max input context length 
        seed_turns = []
        ctx_len = 0
        
        for idx, turn in enumerate(reversed(self.context)):
            if 'text' not in turn:
                log.error(f"Turn {idx} has no 'text': {turn}")
                continue 
            
            turn_len = len(turn['text'].strip().split())
            ctx_len += turn_len
            if ctx_len >= self.max_ctx_len:
                break
            seed_turns = [turn] + seed_turns
            
        return seed_turns      

    def talk(self, timeout=None):
        
        turns = self._get_turns()
        
        new_message_text = self.prompt_generator.run(
            turns,
            self.turn_idx
        )
        new_message_text = new_message_text.strip()
        
        new_message = {
            "user_id": self.prompt_generator.title, 
            "text": new_message_text, 
            "is_seed": False, 
            "episode_done": False
        }

        self.context.append(new_message)
        self.turn_idx += 1
        return new_message 

    def hear(self, msg: Dict):
        self.context.append(msg)
        
    def backspace(self) -> list:
        """
        Used only for experimental cases    
        Returns:
            list(str): list of popped context strings
        """
        self.turn_idx -= 1
        self.prompt_generator.backspace()
        return [self.context.pop() for _ in range(2)]
    
    def force_completion(self):
        """
        Used only for experimental cases
        Returns:
            dict: similar output to talk
        """

        resp = self.endpoints[self.default_endpoint](messages=self.context, engine=self.engine)

        final_message_text = resp
        final_message_text = final_message_text.strip()
        
        final_message = {
            'text': final_message_text,
            'user_id': "Forced Completion",
            'episode_done': False
        }
        self.context.append(final_message)
        return final_message