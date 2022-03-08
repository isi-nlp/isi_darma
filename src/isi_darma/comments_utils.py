import random
from typing import List


def format_dialogue(comment_list: List):
    dialogues = [[comment] for comment in comment_list]
    # print(dialogues)
    while any([d[-1].replies for d in dialogues]):
        new_dialogues = []
        for d in dialogues:
            if not isinstance(d[-1], str) and d[-1].replies:
                new_dialogues += [d + [reply] for reply in d[-1].replies]
            else:
                new_dialogues += [d]
                # dialogues = [d[:-1] + [d[-1].body, reply] for d in dialogues for reply in d[-1].replies]
        dialogues = new_dialogues
        # print(dialogues)

    return dialogues


def get_dialogue_text(dialogue: List):
    return [comment.body for comment in dialogue]

def get_random_comtype_resp(username=None):
    comtype_responses = [
    'Please quit doing that and behave!',
    f'You used this kind of behavior in response to [USERNAME2, USERNAME3, ...]',
    f'You used this kind of behavior in response to [USERNAME2, USERNAME3, ...].',
    f'You used this kind of behavior in response to [USERNAME2, USERNAME3, ...]. I feel upset because even though I don’t know [USERNAME2, USERNAME3...], the language you used when communicating with them would make me upset.',
    f'You used this kind of behavior in response to [USERNAME2, USERNAME3, ...]. Is this because you are angry at  [USERNAME2, USERNAME3, ...] for having beliefs that are different from yours?',
    f'You used this kind of behavior in response to [USERNAME2, USERNAME3, ...]. Is this because you are angry at  [USERNAME2, USERNAME3, ...] for having beliefs that are  different from yours? Do you want  [USERNAME2, USERNAME3, ...] to change their opinions and perhaps convince others who currently share their opinions to also change?'
 ]
    return random.sample(comtype_responses, 1)