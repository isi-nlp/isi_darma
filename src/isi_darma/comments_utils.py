from typing import List 

def format_dialogue(comment_list: List): 

    dialogues = [[comment] for comment in comment_list] 
    # print(dialogues)
    while any([d[-1].replies for d in  dialogues]): 
        new_dialogues =[] 
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