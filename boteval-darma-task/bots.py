"""
This work is done by Taiwei Shi during his internship at USC ISI (Summer 2022).
"""

import openai
import os
import json

from boteval import log, C, registry as R
from boteval.bots import BotAgent
from .prompt_generator import PromptGenerator


@R.register(R.BOT, name="gpt")
class GPTBot(BotAgent):

    def __init__(self, engine: str, persona_id: str,
            *args, api_key='',
            few_shot_example=None, max_ctx_len=2048,
            persona_configs_relative_filepath='persona_configs.json',
            **kwargs):
        super().__init__(*args, name="gpt", **kwargs)
        
        self.max_ctx_len = max_ctx_len
        self.engine = engine
        self.prompt_generator_id = persona_id
        self.few_shot_example = few_shot_example # e.g. nvc

        api_key = api_key or os.environ.get('OPENAI_KEY', '')
        if not api_key:
            raise Exception("OpenAI API key is not set."
                            " Please 'export OPENAI_KEY=<key>' and rerun."
                            " You may obtain key from https://beta.openai.com/account/api-keys")
        openai.api_key = api_key

        self.prompt_generator = self.load_persona(
            persona_id,
            configs_relative_filepath=\
                persona_configs_relative_filepath,
            few_shot_example=self.few_shot_example
        )
        
        self.turn_idx = 0
        log.info(f"Initialized GPT bot with {self.engine=} {self.prompt_generator_id=} {self.prompt_generator.title=}\n{self.prompt_generator.instruction=}")
        self.context = []

    def load_persona(self, 
                     persona_id:str,
                     configs_relative_filepath='persona_configs.json',
                     few_shot_example=None):
        
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
            
            assert len(matching_personas) == 1
            return PromptGenerator(
                matching_personas[0], 
                lambda prompt, **args: self.query_completion_api(
                    prompt, engine=self.engine, **args
                ),
                few_shot_example=few_shot_example)
            
            #     raise Exception(f'Unknown prompt: {prompt}')
        

    def context_append(self, user, text):
        turn = f'user {user}: {text}'
        n_toks = len(turn.strip().split())
        self.context.append((turn, n_toks))

    def get_seed_turns(self) -> str:
        seed_turns = ''
        ctx_len = 0
        for turn, turn_len in reversed(self.context):
            ctx_len += turn_len
            if ctx_len >= self.max_ctx_len:
                break
            seed_turns = turn + '\n' + seed_turns
        return seed_turns.strip()

    def force_completion(self):
        seed_turns = self.get_seed_turns()
        resp = self.query_completion_api(seed_turns, engine=self.engine)

        final_message_text = resp
        final_message_text = final_message_text.strip()
        
        self.feed(final_message_text)
        act_out = {}
        act_out['text'] = final_message_text
        act_out['user_id'] = "Forced Completion"
        return {**act_out, 'episode_done': False}
    
    def talk(self, timeout=None):
        seed_turns = self.get_seed_turns()
        
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
        
    def back_space(self):
        return self.context.pop()
    
    
    @staticmethod
    def query_completion_api(
            prompt, engine,
            frequency_penalty=0, presence_penalty=0,
            temperature=0.7, n=1
        ):
        max_timeout_rounds = 5
        for _ in range(max_timeout_rounds):
            # GPT-3 Generation
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
