import os
import openai
from darma_chat.bot_agent import TurkLikeAgent, logging

DEF_ENGINE = 'text-davinci-002'  # TODO: get this from yaml file


class TurkLikeGptAgent(TurkLikeAgent):
    """
    Will act like a Turker but connects to OpenAI GPT API
    """

    def __init__(self, *args, api_key='', engine=DEF_ENGINE, **kwargs):
        super().__init__(*args, **kwargs)
        self.sturns = ''
        self.engine = engine
        if not api_key:
            api_key = os.environ.get('OPENAI_KEY', '')
        if not api_key:
            raise Exception("OpenAI API key is not set."
                            " Please 'export OPENAI_KEY=<key>' and rerun."
                            " You may obtain key from https://beta.openai.com/account/api-keys")
        openai.api_key = api_key


    def act(self, timeout=None):
        instr = "The following is a conversation with a wise and loving being who has an understanding of how nonviolent communication work. This being is dedicated to building a more civil online environment."
        if self.turn_idx == 0:
            few_shot_example = "user A: Does this look like a normal poop? Worried\nuser B: I was happily scrolling my feed until I came across this - dude, put the NFSW on! 🤮\nuser A: Get fucked\nwise being: it sounds like you're worried about your poop and you're wondering if it is normal. Can you tell me more about it?"
        else:
            few_shot_example = ""
        p = self.prompt_compose(instr, few_shot_example, self.sturns)
        # print("#" * 30)
        # print(p)
        if self.turn_idx == 0:
            resp = self.query_completion_api(p, engine=self.engine)
        else:
            resp = self.query_completion_api(
                p, engine=self.engine, frequency_penalty=1, presence_penalty=1, temperature=1)
        final_message_text = resp.choices[0].text
        final_message_text = final_message_text.strip()
        self.sturns += f"wise being: {final_message_text}\n"

        act_out = {}
        act_out['text'] = final_message_text
        act_out['id'] = "BOT"
        self.turn_idx += 1
        return {**act_out, 'episode_done': False}

    def observe(self, observation, increment_turn: bool = True):
        self.sturns += f"user {observation['id']}: {observation['text']}\n"

    @staticmethod
    def query_completion_api(prompt, engine=DEF_ENGINE,
                             frequency_penalty=0, presence_penalty=0, temperature=0):
        response = openai.Completion.create(
            model=engine,
            prompt=prompt,
            temperature=temperature,
            max_tokens=512,
            top_p=1,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        return response

    @staticmethod
    def prompt_compose(instr, few_shot_example, seed_turns):
        if few_shot_example == "":
            return f'{instr}\n\n{seed_turns}wise being:'
        return f'{instr}\n\n{few_shot_example}\n\n{seed_turns}wise being:'
