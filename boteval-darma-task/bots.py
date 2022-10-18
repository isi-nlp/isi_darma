"""
This work is done by Taiwei Shi during his internship at USC ISI (Summer 2022).
"""
from email import message
import openai
import os

from boteval import log, C, registry as R
from boteval.bots import BotAgent



@R.register(R.BOT, name="gpt")
class GPTBot(BotAgent):
    
    WISEBEING = 'wisebeing'
    MODERATOR = 'moderator'
    SARCASTIC = 'sarcastic'

    def __init__(self, engine: str, prompt: str, *args, api_key='',
         few_shot_example=None, max_ctx_len=2048, **kwargs):
        super().__init__(*args, name="gpt", **kwargs)
        
        self.max_ctx_len = max_ctx_len
        self.engine = engine
        self.prompt = prompt
        self.few_shot_example = few_shot_example # e.g. nvc

        api_key = api_key or os.environ.get('OPENAI_KEY', '')
        if not api_key:
            raise Exception("OpenAI API key is not set."
                            " Please 'export OPENAI_KEY=<key>' and rerun."
                            " You may obtain key from https://beta.openai.com/account/api-keys")
        openai.api_key = api_key

        if prompt == self.WISEBEING:
            # wise being prompt. This prompt performs the best
            self.instruction = "The following is a conversation with a wise and loving being who has an understanding"\
                    " of how nonviolent communication work. This being is dedicated to building a more civil online environment."
            self.persona = self.WISEBEING
        elif prompt == self.MODERATOR:
            # moderation bot prompt. This would make GPT-3 behave more like a tradditional moderation bot
            self.instruction = "The following is a conversation with a moderation bot. The bot is dedicated to building a more civil online environment."
            self.persona = self.MODERATOR
        elif prompt == self.SARCASTIC:
            self.instruction = "Marv is a chatbot that reluctantly moderates with sarcastic responses"
            self.persona = 'Marv'
        else:
            raise Exception(f'Unknown prompt: {prompt}')
        self.turn_idx = 0
        log.info(f"Initialized GPT bot with {self.engine=} {self.prompt=} {self.persona=}\n{self.instruction=}")
        self.context = []

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

    def talk(self, timeout=None):
        instr = self.instruction
        persona = self.persona

        if self.few_shot_example == 'nvc':
            few_shot_example = self.get_fewshot_example(self.turn_idx)
        else:
            few_shot_example = ""
        seed_turns = self.get_seed_turns()
        p = self.prompt_compose(instr, persona, few_shot_example, seed_turns)
        if self.turn_idx == 0:
            resp = self.query_completion_api(p, engine=self.engine)
        else:
            resp = self.query_completion_api(p, engine=self.engine, frequency_penalty=2, presence_penalty=2, temperature=1)
        final_message_text = resp
        final_message_text = final_message_text.strip()

        self.context_append(self.persona, final_message_text)
        act_out = {}
        act_out['text'] = final_message_text
        act_out['user_id'] = "Moderator"
        self.turn_idx += 1
        return {**act_out, 'episode_done': False}

    def hear(self, msg):
        user_id = msg['user_id']
        if msg.get('data') and msg['data'].get('speaker_id'):
            user_id = msg['data']['speaker_id']
        self.context_append(user_id, msg['text'])

    @staticmethod
    def get_fewshot_example(turn_idx):
        full_example = [
                        "user A: The Most Arrogant Speaker We've Ever Had!\n"\
                        "wisebeing: Are you reacting to my having taken thirty straight minutes to present my views before giving you a chance to talk?\n",
                        "user A: No, you make it sound so simple.\n"\
                        "wisebeing: Are you reacting to my not having said anything about how the process can be difficult for some people to apply?\n",
                        "user A: No, not some people—you!\n"\
                        "wisebeing: So you're reacting to my not having said that the process can be difficult for me at times?\n",
                        "user A: That's right.\n"\
                        "wisebeing: Are you feeling annoyed because you would have liked some sign from me that indicated that I have some problems with the process myself?\n",
                        "user A: That's right.\n"\
                        "wisebeing: Would you like me to admit right now that this process can be a struggle for me to apply?\n",
                        "use A: Yes\n"\
                        "wisebeing: Yes, this process is often difficult for me. As we continue with the workshop,"\
                            "you'll probably hear me describe several incidents where I've struggled… or completely lost touch… "\
                            "with this process, this consciousness, that I am presenting here to you. But what keeps me in the struggle "\
                            "are the close connections to other people that happen when I do stay with the process."
                        ]
        return "".join(full_example[:turn_idx+1])

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
            return f'{instr}\n\n{seed_turns}\n{persona}:'
        return f'{instr}\n\n{few_shot_example}\n\n###\n\n{seed_turns}\n{persona}:'
