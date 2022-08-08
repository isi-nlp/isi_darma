from darma_chat.bot_agent import TurkLikeAgent, logging
import openai



class TurkLikeGptAgent(TurkLikeAgent):
    """
    Will act like a Turker but actually contains a bot agent.
    """

    def __init__(self, *args, api_key='', **kwargs):
        super().__init__(*args, **kwargs)
        openai.api_key = api_key

    def act(self, timeout=None):
        instr = "Respond to the last user using nonviolent communication"
        if self.turn_idx == 0:
            few_shot_example = "user 1: Does this look like a normal poop? Worried\nuser 2: I was happily scrolling my feed until I came across this - dude, put the NFSW on! 🤮\nuser 1: Get fucked\nYou: it sounds like you're worried about your poop and you're wondering if it is normal. Can you tell me more about it?"
        else:
            few_shot_example = ""
        p = prompt_compose(instr, few_shot_example, self.sturns)
        if self.turn_idx == 0:
            resp = query_completion_api(p)
        else:
            resp = query_completion_api(p, frequency_penalty=0, presence_penalty=0)
        final_message_text = resp.choices[0].text 
        final_message_text = final_message_text.strip()
        self.sturns += f"you: {final_message_text}\n"

        act_out = {}
        act_out['text'] = final_message_text
        act_out['id'] = "BOT"
        self.turn_idx += 1
        return {**act_out, 'episode_done': False}

    def observe(self, observation, increment_turn: bool = True):
        self.sturns += f"user {observation['id']}: {observation['text']}\n"


def query_completion_api(prompt, engine='text-davinci-002', frequency_penalty=0, presence_penalty=0):
    response = openai.Completion.create(
        model=engine,
        prompt=prompt,
        temperature=0.7,
        max_tokens=512,
        top_p=1,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    return response

def prompt_compose(instr, few_shot_example, seed_turns):
    if few_shot_example == "":
        return f'{instr}\n\n{seed_turns}You:'
    return f'{instr}\n\n{few_shot_example}\n\n{seed_turns}You:'
