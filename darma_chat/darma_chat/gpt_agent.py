import os
import openai
from darma_chat.bot_agent import TurkLikeAgent, logging

# DEF_ENGINE = 'text-davinci-002'  # TODO: get this from yaml file


class TurkLikeGptAgent(TurkLikeAgent):
    """
    Will act like a Turker but connects to OpenAI GPT API
    """

    def __init__(self, *args, api_key='', **kwargs):
        super().__init__(*args, **kwargs)
        self.sturns = ''
        self.engine = self.opt['gpt_engine']
        if not api_key:
            api_key = os.environ.get('OPENAI_KEY', '')
        if not api_key:
            raise Exception("OpenAI API key is not set."
                            " Please 'export OPENAI_KEY=<key>' and rerun."
                            " You may obtain key from https://beta.openai.com/account/api-keys")
        openai.api_key = api_key

        if self.opt['gpt_prompt'] == 'wisebeing':
            # wise being prompt. This prompt performs the best
            self.instruction = "The following is a conversation with a wise and loving being who has an understanding"\
                    " of how nonviolent communication work. This being is dedicated to building a more civil online environment."
            self.gpt_persona = 'wisebeing'
        elif self.opt['gpt_prompt'] == 'moderator':
            # moderation bot prompt. This would make GPT-3 behave more like a tradditional moderation bot
            self.instruction = "The following is a conversation with a moderation bot. The bot is dedicated to building a more civil online environment."
            self.gpt_persona = 'moderation bot'
        elif self.opt['gpt_prompt'] == 'sarcastic':
            self.instruction = "Marv is a chatbot that reluctantly moderates with sarcastic responses"
            self.gpt_persona = 'Marv'

    def act(self, timeout=None):
        instr = self.instruction
        persona = self.gpt_persona
        if self.turn_idx == -1: # make it never happen. At the current stage, we don't want to use the few-show example
            few_shot_example = "user A: Does this look like a normal poop? Worried\n"\
                                "user B: I was happily scrolling my feed until I came across this - dude, put the NFSW on! 🤮\n"\
                                "user A: Get fucked\n"\
                                "wise being: it sounds like you're worried about your poop and you're wondering if it is normal. "\
                                "Can you tell me more about it?"
        else:
            few_shot_example = ""
        p = self.prompt_compose(instr, persona, few_shot_example, self.sturns)
        if self.turn_idx == 0:
            resp = self.query_completion_api(p, engine=self.engine)
        else:
            resp = self.query_completion_api(p, engine=self.engine, frequency_penalty=2, presence_penalty=2, temperature=1)
        final_message_text = resp
        final_message_text = final_message_text.strip()
        self.sturns += f"\n{persona}: {final_message_text}"

        act_out = {}
        act_out['text'] = final_message_text
        act_out['id'] = "Moderator"
        self.turn_idx += 1
        return {**act_out, 'episode_done': False}

    def observe(self, observation, increment_turn: bool = True):
        self.sturns += f"\nuser {observation['id']}: {observation['text']}"

    @staticmethod
    def query_completion_api(prompt, engine,
                             frequency_penalty=0, presence_penalty=0, temperature=0.7):
        max_timeout_rounds = 5
        for _ in range(max_timeout_rounds):
            # GPT-3 Generation
            response = openai.Completion.create(
                model=engine,
                prompt=prompt,
                temperature=temperature,
                max_tokens=1024,
                top_p=1,
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

    @staticmethod
    def prompt_compose(instr, persona, few_shot_example, seed_turns):
        if few_shot_example == "":
            return f'{instr}\n\n{seed_turns}{persona}:'
        return f'{instr}\n\n{few_shot_example}\n\n{seed_turns}\n{persona}:'
