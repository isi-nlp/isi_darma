""" 
TODO: Still under construction
A script meant for interactive analysis and automated processes for fast experiments

@author: Basem Rizk

"""

import os
import json
import textwrap
import logging

from bots import GPTBot

def print_wrap_text(txt, width=99,
                    prefix='#', 
                    subsequent_indent=' ',
                    print_border=False,
                    title=''):
    if print_border:
        print('='*(width+1))
    if title:
        print(f'{prefix} {title}')
    for s in textwrap.wrap(txt, width=99,
                           subsequent_indent=subsequent_indent):
        print(f'{prefix} {s}')
    if print_border:
        print('='*(width+1))

def pick_valid_choice(alist, statement='Enter config #: '):
    num = -1
    while num < 1 or num >= len(alist):
        try:
            num = int(input(statement))  
        except:
            print('Please enter appropriate value.')    
    return alist[num-1]

def load_persona_confs(confs_filename='persona_configs.json'):
    with open(confs_filename) as f:
        confs_json = json.load(f)
        # json_formatted_str = json.dumps(conf_json, indent=2)
        # print(json_formatted_str)
        for i, conf in enumerate(confs_json):
            print("="*100)
            print(f'# {i+1} :: id({conf["id"]})')
            print(f'# Notes: {conf["notes"]}')
            print(f'# Title: {conf["title"]}')
            print('# Instruction:')
            print_wrap_text(conf['instruction'])
            print("="*100)
        
    choice = pick_valid_choice(confs_json)
    persona_id = choice['id']
    persona_title = choice['title']
    persona_instruction = choice['instruction']
    return persona_id, persona_title, persona_instruction

def load_conversation(filename='chat_topics_eng.json'):
    with open(filename) as f:
        convs_json = json.load(f)

    print('# Pick')
    print_wrap_text(
        str([c['id'] for c in convs_json]),
        print_border=True,
        title='Conversation IDs'
        )
    choice = 0 #pick_valid_choice(convs_json, statement='Enter conv ID:')
    conv = convs_json[choice]
    
    print(f'Conversation ID: {conv["id"]}')
    print(f'Conversation Name: {conv["name"]}')
    
    # def prepare_msg(json_obj):
    #     return {
    #         'user_id': json_obj['speaker_id'],
    #         'data': json_obj['text'] 
    #     }
    #     # return f"User {json_obj['speaker_id']}: {json_obj['text']}"
    
    # conv = [
    #     prepare_msg(j) for j in conv['conversation']
    # ]
    
    return conv

def interactive_session(
        engine='text-davinci-003',
        max_ctx_len=2048
    ):
    while(True):
        persona_id, persona_title, persona_instruction = load_persona_confs()

        bot = GPTBot(
            engine=engine,
            prompt=persona_id,
            # title=persona_title,
            # instruction=persona_instruction,
            # few_shot_example=existing_conv,
            max_ctx_len=max_ctx_len,
        )
        
        print(f'Conversation ID: {existing_conv["id"]}')
        print(f'Conversation Name: {existing_conv["name"]}')
        print('='*100)
        for msg in existing_conv['conversation']:
            bot.hear(msg)
            print_wrap_text(f'User {msg["speaker_id"]}: {msg["text"]}')
            final_user = msg['speaker_id']
            print('='*100)
        reply = bot.talk()
        print_wrap_text(f'User {persona_title}: {reply["text"]}')
        print('='*100)

        
        while True:
            line = input(f'[User {final_user}]: ')
            line = line.strip()
            if not line:
                continue
            if line == "exit":
                break
            if line.startswith("\\\\"):
                bot.feed(line[2:])
            else:
                bot.hear({
                    'speaker_id': final_user,
                    'text': line
                })
            print('='*100)
            reply = bot.talk()
            print_wrap_text(f'User {persona_title}: {reply["text"]}')
            print('='*100)

        
        query = input('Do you want to continue? ')
        if query.lower() in ['q', 'quit']:
            print('Quitting')
            break
        

def load_chats_per_id(chat_dir, conv_id, n=3):
    convs_filepaths = []
    for root, dirs, files in os.walk(chat_dir, topdown=False):
        for f in files:
            if conv_id in f:
                convs_filepaths.append(os.path.join(root, f))
                
    convs_cleaned = []
    for f in convs_filepaths[-n:]:
        with open(f, mode='r') as f:
            conv_json = json.load(f)
            msgs_prepared = []
            for msg in conv_json['messages']:
                # If not created by mturker
                if msg.get('data') and msg['data'].get('speaker_id'):
                    speaker_id = msg['data']['speaker_id']
                    org_text = True
                else:
                    speaker_id = msg['user_id']
                    org_text = False
                
                msgs_prepared.append({
                    'org_text': org_text,
                    'speaker_id': speaker_id,
                    'text': msg['text']
                })
                
            convs_cleaned.append(msgs_prepared)
    return convs_cleaned
        
        
        
if __name__ == "__main__":
    
    existing_conv = load_conversation()
    mturk_data_dir = '/mnt/c/Users/basem/Projects/ISI/isi_darma/boteval-darma-task/data/data'
    # logging.getLogger().setLevel(logging.CRITICAL)
    # interactive_session()
    # mturk_chats = load_chats_per_id(mturk_data_dir, existing_conv['id'])
    # TODO inject mturk responses into conversation
    # breakpoint()
    interactive_session()
    
    
