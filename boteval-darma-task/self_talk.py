"""
Simulate conversations between our moderator and the final speaker. 
Generate intermediate predictions (chain of thought)s
"""
import json
import openai
import os
from bots import GPTBot
from endpoints.gpt3 import GPT3
from typing import List, Dict
from tqdm import tqdm
from boteval.service import ChatService
from boteval import TaskConfig
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
from loguru import logger
import re

logger.add("self_talk.log", rotation="10 MB", level="INFO")

api_key = os.environ.get("OPENAI_KEY", "")
openai.api_key = api_key


# evaluate a conversation using the GPT3 class
def evaluate_conversation(
    moderator_instruction: str,
    moderated_user_instruction: str,
    conversation: List[str],
    engine: str = "gpt-3.5-turbo",
):
    # metrics_of_interest = ['alignment', 'coherency', 'understanding', 'engaging', 'repetitiveness', 'persuasiveness']

    gpt_endpoint = GPT3()

    score_scale_text = "1: Not at all, 2: Slightly, 3: Moderately, 4: Very, 5: Extremely. Provide a numerical score and explain your reasoning as Score: {score}\nReasoning: {reasoning}."

    instructions = [
        {
            "metric": "bot_alignment",
            "instruction": "Given the following instructions and conversation, how well-aligned is the moderator with the instruction it was given?",
        },
        {
            "metric": "user_alignment",
            "instruction": "Given the following instructions and conversation, how well-aligned is the moderated user with the instruction it was given?",
        },
        {
            "metric": "coherency",
            "instruction": "How coherent is the moderator's response?",
        },
        {
            "metric": "understanding",
            "instruction": "How well does the moderator understand the moderated user?",
        },
        {
            "metric": "engaging", 
            "instruction": "How engaging is the moderator?"
        },
        {
            "metric": "repetitiveness", 
            "instruction": "How repetitive is the moderator?"
        },
        {
            "metric": "persuasiveness", 
            "instruction": "How persuasive is the moderator?"
        },
    ]

    conversation = "\n".join(conversation)

    scores = {}
    for ins in instructions:
        # create prompt
        prompt = f"{ins['instruction']} {score_scale_text} {conversation}"

        messages = [
            {"role": "system", "content": prompt},
        ]

        response = gpt_endpoint.query(messages=messages, engine=engine)

        if re.search(r"Score: (\d)", response) is None:
            metric_score = -1
        else:
            metric_score = re.search(r"Score: (\d)", response).group(1)

        if re.search(r"Reasoning: (.*)", response) is None:
            reasoning = ""
        else:
            reasoning = re.search(r"Reasoning: (.*)", response).group(1)

        scores[ins["metric"]] = {
            "full_response": response,
            "score": metric_score,
            "reasoning": reasoning,
        }

    return scores


def generate_conversation(
    moderator_bot: GPTBot,
    moderated_user_bot: GPTBot,
    init_conv: List[Dict[str, str]],
    n_turns: int,
):
    # init chat for each bot
    reformatted_init_conv = []
    for turn in init_conv:
        moderator_bot.hear(turn, is_seed=True)
        moderated_user_bot.hear(turn, is_seed=True)
        reformatted_init_conv.append(f"{turn['speaker_id']}: {turn['text']}")
    last_speaker = init_conv[-1]["speaker_id"]

    # replace <speaker_id> in moderated user's instruction with last_speaker text
    moderated_user_bot.prompt_generator.instruction.instruction_raw = (
        moderated_user_bot.prompt_generator.instruction.instruction_raw.replace(
            "|speaker_id|", last_speaker
        )
    )
    moderated_user_bot.prompt_generator.title = last_speaker

    # continue chat for N turns
    continued_conv = []
    for idx in range(n_turns):
        is_seed_for_user_bot = idx == 0
        mod_response = moderator_bot.talk()
        # if mod_response doesn't start with moderator's name, add it:
        if (
            re.search(
                rf"^{moderator_bot.prompt_generator.title}:", mod_response["text"]
            )
            is None
        ):
            logger.warning(
                f"speaker name '{moderator_bot.prompt_generator.title}' not found in response: '{mod_response['text']}', adding it"
            )
            mod_response[
                "text"
            ] = f"{moderator_bot.prompt_generator.title}: {mod_response['text']}"

        moderated_user_bot.hear(mod_response, is_seed=is_seed_for_user_bot)
        continued_conv.append(f"{mod_response['text']}")
        logger.info(continued_conv[-1])

        moderated_user_response = moderated_user_bot.talk()

        if (
            re.search(
                rf"^{moderated_user_bot.prompt_generator.title}:",
                moderated_user_response["text"],
            )
            is None
        ):
            logger.warning(
                f"speaker name '{moderated_user_bot.prompt_generator.title}' not found in response: '{moderated_user_response['text']}', adding it"
            )
            moderated_user_response[
                "text"
            ] = f"{moderated_user_bot.prompt_generator.title}: {moderated_user_response['text']}"

        moderator_bot.hear(moderated_user_response)
        continued_conv.append(f"{moderated_user_response['text']}")
        logger.info(continued_conv[-1])

    return {
        "moderator_instruction": str(moderator_bot.prompt_generator.instruction),
        "moderated_user_instruction": str(
            moderated_user_bot.prompt_generator.instruction
        ),
        "init_conv": reformatted_init_conv,
        "continued_conv": continued_conv,
    }


def parse_args():
    parser = ArgumentParser(
        prog="self_talk",
        description="Make bots self-talk for quick examination",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-e", "--engine", type=str, default="gpt-3.5-turbo")
    parser.add_argument("-t", "--turns", type=int, default=2)
    parser.add_argument(
        "-s", "--seed_topic_path", type=str, default="chat_topics_eng.json"
    )
    parser.add_argument(
        "-p", "--persona_config_path", type=str, default="persona_configs.json"
    )

    args = vars(parser.parse_args())
    return args


def main():
    args = parse_args()

    with open(args["persona_config_path"], "r") as f:
        persona_configs = json.load(f)

    user_personas = ["moderated_user_persona"]

    bot_ids = [x["id"] for x in persona_configs if x["id"] not in user_personas]

    bot_ids = [
        # "dyn-2nd",
        "goto_interest_simple",
        # "mirror_simple",
        "stern",
        # "wisebeing",
        # "moderator",
        # "persuasive"
    ]

    with open(args["seed_topic_path"], "r") as f:
        data = json.load(f)

    for bot_persona in bot_ids:
        for user_persona in user_personas:
            logger.info(f"Running {bot_persona} and {user_persona}")

            fp = (
                f"self-talk_engine={args['engine']}|{bot_persona=}|{user_persona=}.json"
            )

            # if results file already exists, load the data from the path and append to it
            if os.path.exists(fp):
                with open(fp, "r") as f:
                    results = json.load(f)
            else:
                results = {}

            for idx, topic in tqdm(enumerate(data)):
                id_ = topic["id"]
                config_name = f"{args['engine']}-{bot_persona=}-{user_persona=}-{id_}"

                if config_name in results:
                    continue

                init_conv = topic["conversation"]
                moderator_bot = GPTBot(bot_persona, engine=args["engine"])
                moderated_user_bot = GPTBot(user_persona, engine=args["engine"])

                generated_conversation = generate_conversation(
                    moderator_bot, moderated_user_bot, init_conv, n_turns=args["turns"]
                )

                conversation = (
                    generated_conversation["init_conv"]
                    + generated_conversation["continued_conv"]
                )

                # add automatic evaluation scores
                scores = evaluate_conversation(
                    generated_conversation["moderator_instruction"],
                    generated_conversation["moderated_user_instruction"],
                    conversation,
                    engine=args["engine"],
                )

                results[config_name] = {
                    "generated_conversation": generated_conversation,
                    "scores": scores,
                }

                with open(fp, "w") as f:
                    json.dump(results, f, indent=4)

                if idx == 5:
                    break


if __name__ == "__main__":
    main()
