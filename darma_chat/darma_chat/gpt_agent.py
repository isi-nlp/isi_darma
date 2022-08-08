from parlai.core.params import ParlaiParser
import openai  

from typing import Dict

from omegaconf import DictConfig
import parlai.utils.logging as logging
from parlai.core.agents import create_agent
from parlai.core.params import ParlaiParser
from darma_chat.constants import AGENT_1


class TurkLikeGptAgent:
    """
    Will act like a Turker but actually contains a bot agent.
    """

    def __init__(self, opt, model_name, num_turns, semaphore=None):
        self.opt = opt
        self.id = AGENT_1
        self.num_turns = num_turns
        self.turn_idx = 0
        self.semaphore = semaphore
        self.worker_id = model_name
        self.hit_id = 'none'
        self.assignment_id = 'none'
        self.some_agent_disconnected = False
        self.hit_is_abandoned = False
        self.hit_is_returned = False
        self.disconnected = False
        self.hit_is_expired = False
        self.sturns = ''
        openai.api_key = '' 

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

    def shutdown(self):
        pass

    def reset(self):
        self.model_agent.reset()

    @staticmethod
    def get_bot_agents(
        args: DictConfig, model_opts: Dict[str, str], no_cuda=False
    ) -> Dict[str, dict]:
        """
        Return shared bot agents.

        Pass in model opts with the `model_opts` arg, where `model_opts` is a dictionary
        whose keys are model names and whose values are strings that specify model
        params (i.e. `--model image_seq2seq`).
        """

        # Set up overrides
        model_overrides = {'model_parallel': args.blueprint.task_model_parallel}
        if no_cuda:
            # If we load many models at once, we have to keep it on CPU
            model_overrides['no_cuda'] = no_cuda
        else:
            logging.warning(
                'WARNING: MTurk task has no_cuda FALSE. Models will run on GPU. Will '
                'not work if loading many models at once.'
            )

        # Convert opt strings to Opt objects
        processed_opts = {}
        for name, opt_string in model_opts.items():
            parser = ParlaiParser(True, True)
            parser.set_params(**model_overrides)
            processed_opts[name] = parser.parse_args(opt_string.split())

        # Load and share all model agents
        logging.info(
            f'Got {len(list(processed_opts.keys()))} models: {processed_opts.keys()}.'
        )
        shared_bot_agents = {}
        for model_name, model_opt in processed_opts.items():
            logging.info('\n\n--------------------------------')
            logging.info(f'model_name: {model_name}, opt_dict: {model_opt}')
            model_agent = create_agent(model_opt, requireModelExists=True)
            shared_bot_agents[model_name] = model_agent.share()
        return shared_bot_agents

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
