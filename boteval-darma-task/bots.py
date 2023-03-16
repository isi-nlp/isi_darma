"""
This work is done by Taiwei Shi during his internship at USC ISI (Summer 2022).
"""

import os
import json

import endpoints
from prompt_generator import PromptGenerator
from boteval import log, C, registry as R
from boteval.bots import BotAgent

@R.register(R.BOT, name="gpt")
class GPTBot(BotAgent):

    def __init__(self, persona_id: str,
            *args, engine: str=None, api_key='',
            default_endpoint='gpt3',
            few_shot_example=None, max_ctx_len=2048,
            persona_configs_relative_filepath='persona_configs.json',
            **kwargs):
        super().__init__(*args, name="gpt", **kwargs)
        
        self.max_ctx_len = max_ctx_len
        self.few_shot_example = few_shot_example # e.g. nvc
        self.default_endpoint = default_endpoint
        self.engine = engine 
        
        if engine:
            os.environ['OPENAI_ENGINE'] = engine
        
        if api_key:
            # Read by endpoint implementation
            os.environ['OPENAI_KEY'] = api_key

        self.setup_endpoints()
        
        self.prompt_generator = self.load_persona(
            persona_id,
            configs_relative_filepath=\
                persona_configs_relative_filepath,
        )
        
        self.turn_idx = 0
        self.context = []
        
        log.info(
            f"Initialized GPT bot with {engine=}"
            f"{self.prompt_generator.id=}"
            f"{self.prompt_generator.title=}\n"
            f"{self.prompt_generator.instruction.instruction_raw=}")
        

    def setup_endpoints(self):
        self.endpoints = endpoints.endpoints_dict        
        endpoints_listing = "\n".join([
            f"- {k}" for k in self.endpoints.keys()
        ])
        log.info(
            f"Available endpoints:\n\t{endpoints_listing}\n"
            f"\twhile default is {self.default_endpoint}"
        )

    def load_persona(self, 
                     persona_id:str,
                     configs_relative_filepath='persona_configs.json'):
        
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

            return PromptGenerator(
                matching_personas[0], 
                self.endpoints,
                self.engine,
                default_endpoint=self.default_endpoint,
                few_shot_example=self.few_shot_example
            )

    def context_append(self, user, text):
        turn = f'user {user}: {text}'
        n_toks = len(turn.strip().split())
        self.context.append((turn, n_toks))
    
    
    def _get_seed_turns(self, context) -> str:
        # truncate to not exceed max input context length 
        seed_turns = []
        ctx_len = 0
        
        for turn, turn_len in reversed(context):
            ctx_len += turn_len
            if ctx_len >= self.max_ctx_len:
                break
            seed_turns = [turn] + seed_turns
        return seed_turns      

    def talk(self, timeout=None):
        
        seed_turns = self._get_seed_turns(self.context)
        
        final_message_text = self.prompt_generator.run(
            seed_turns,
            self.turn_idx
        )
        final_message_text = final_message_text.strip()

        self.context_append(self.prompt_generator.title, final_message_text)
        act_out = {}
        act_out['text'] = final_message_text
        act_out['user_id'] = "Moderator"
        self.turn_idx += 1
        return {**act_out, 'episode_done': False}

    def hear(self, msg):
        user_id = msg.get('user_id')
        if msg.get('data') and msg['data'].get('speaker_id'):
            user_id = msg['data']['speaker_id']
        if not user_id and msg.get('speaker_id'):
            user_id = msg['speaker_id']
        self.context_append(user_id, msg['text'])

    def feed(self, text):
        # force feed instead of adding conversation
        n_toks = len(text.strip().split())
        self.context.append((text, n_toks))
        
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

        resp = self.endpoints[self.default_endpoint](self.context)

        final_message_text = resp
        final_message_text = final_message_text.strip()
        
        self.feed(final_message_text)
        act_out = {}
        act_out['text'] = final_message_text
        act_out['user_id'] = "Forced Completion"
        return {**act_out, 'episode_done': False}