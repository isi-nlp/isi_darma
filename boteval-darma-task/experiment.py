""" 
TODO: Still under construction
A script meant for interactive analysis and automated processes for fast experiments

@author: Basem Rizk

"""

import os
import json
import textwrap
import logging
import argparse
import numpy as np

from bots import GPTBot
from tabulate import tabulate

PRINT_WIDTH=-1 # Modified by argparse

class MixedBots:
    
    def __init__(self, personas, engine, max_ctx_len,
                 print_width=100):
        # personas = [(<id>, <title>, <insturction>), ..]
        self.personas = personas
        self.ids = []
        self.titles = []
        for p in personas:
            self.ids.append(p[0])
            self.titles.append(p[1])
            
        self.bots = [
            GPTBot(
                engine=engine,
                prompt=persona_id,
                # title=persona_title,
                # instruction=persona_instruction,
                # few_shot_example=existing_conv,
                max_ctx_len=max_ctx_len,
            )
            for persona_id, _, _ in self.personas
        ]
        self.print_width = print_width
        self.sub_width =\
            int((self.print_width-1)/len(self.personas))

        
    def __len__(self) -> int:
        return len(self.bots)
    
    def __getitem__(self, i: int) -> GPTBot:
        return self.bots[i]
    
    def print_personas(self) -> str:
        personas_table = [[], []]
        instruction_table = []
        print('='*self.print_width)
        for id, title, instruction in self.personas:
            personas_table[0].append(id)
            personas_table[1].append(title)
            instruction_table.append(textwrap.wrap(instruction, width=self.sub_width))
        
        instruction_table = self.fill_table(instruction_table)
        personas_table = np.vstack([
            personas_table,
            instruction_table.T
        ]) 
        del instruction_table
            
        print(tabulate(personas_table, headers="firstrow"))
        print('='*self.print_width)
    
    @staticmethod
    def fill_table(ndlist) -> np.array:
        max_lines = max(map(len, ndlist)) 
        for l in ndlist:
            l += ['']*(max_lines-len(l))
        return np.array(ndlist)
    
    def _iterate(self, func):
        outcome = []
        for b in self.bots:
            outcome.append(func(b))
        return outcome
            
    def hear(self, msg):     
        self._iterate(lambda x: x.hear(msg))       
    
    def feed(self, txt):     
        self._iterate(lambda x: x.feed(txt))     
          
    def talk(self, verbose=True):     
        replies = self._iterate(lambda x: x.talk())

        if verbose:
            table = self.fill_table([
                textwrap.wrap(
                    f'User {x[0]}: {x[1]["text"]}',
                    width=self.sub_width
                ) for x in zip(self.titles, replies)
            ])
            table = np.vstack([
                self.ids,
                table.T
            ]) 
            print(tabulate(table, headers="firstrow"))
            print('='*self.print_width)
        
        return replies
        
            
def print_wrap_text(txt, width=None,
                    prefix='#', 
                    subsequent_indent=' ',
                    print_border=False,
                    title=''):
    if not width:
        width=PRINT_WIDTH
    if print_border:
        print('='*(width+1))
    if title:
        print(f'{prefix} {title}')
    for s in textwrap.wrap(txt, width=width,
                           subsequent_indent=subsequent_indent):
        print(f'{prefix} {s}')
    if print_border:
        print('='*(width+1))

def pick_valid_choice(alist, statement='Enter config #: '):
    def is_valid(x):
        return x >= 0 and x < len(alist)
    def verified_input(xs):
        valids = list(map(lambda x: is_valid(x), xs))
        return np.prod(valids) and len(xs) > 0
    nums = []
    while not verified_input(nums):
        try:
            selection = input(statement)
            nums = list(map(
                lambda x: int(x)-1,
                selection.split(',')
            ))
        except:
            print('Please enter appropriate value.')    
    return list(map(alist.__getitem__, nums))

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
        
    choices = pick_valid_choice(confs_json)
    personas = [
        (c['id'], c['title'], c['instruction'])
        for c in choices
    ]
    return personas

def load_conversation(filepath='chat_topics_eng.json', conv_id=None):
    with open(filepath) as f:
        convs_json = json.load(f)

    print('# Pick')
    print_wrap_text(
        str([c['id'] for c in convs_json]),
        print_border=True,
        title='Conversation IDs',
    )
    
    if conv_id:
        choice = [
            i for i, c in enumerate(convs_json) 
            if c['id'] == conv_id
        ][0]
    else:
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
        personas = load_persona_confs()
        bots = MixedBots(
            personas, 
            engine=engine,
            max_ctx_len=max_ctx_len, 
            print_width=PRINT_WIDTH
        )
        bots.print_personas()
        
        print(f'Conversation ID: {existing_conv["id"]}')
        print(f'Conversation Name: {existing_conv["name"]}')
        print('='*PRINT_WIDTH)
        for msg in existing_conv['conversation']:
            bots.hear(msg)
            print_wrap_text(f'User {msg["speaker_id"]}: {msg["text"]}')
            final_user = msg['speaker_id']
            print('='*PRINT_WIDTH)
        replies = bots.talk()

        
        while True:
            line = input(f'[User {final_user}]: ')
            line = line.strip()
            if not line:
                continue
            if line == "exit":
                break
            if line.startswith("\\\\"):
                bots.feed(line[2:])
            else:
                bots.hear({
                    'speaker_id': final_user,
                    'text': line
                })
            print('='*PRINT_WIDTH)
            reply = bots.talk()

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
    
    parser = argparse.ArgumentParser(description='Alignment Options and Configs.')
    parser.add_argument('-inter', default=True, type=bool,
                        help='Run interactive session')
    parser.add_argument('-conv_id',  default='chat51', type=str,
                        help='Selected conversation id')
    parser.add_argument('-conv_file', default='chat_topics_eng.json', type=str,
                        help='Conversations filepath')
    parser.add_argument('-print_width',  default=150, type=int,
                        help='Debug printing width')
    parser.add_argument('-suppress_log',  default=True, type=bool,
                        help='Supress logs including warning and info of OpenAI')
    parser.add_argument('-write_log',  default=True, type=bool,
                        help='TODO write what has printed')
    args = parser.parse_args()
    
    PRINT_WIDTH = args.print_width
    
    if args.suppress_log:
            logging.getLogger().setLevel(logging.CRITICAL)
            
    if args.inter:
        existing_conv = load_conversation(filepath=args.conv_file, conv_id=args.conv_id)
        mturk_data_dir = '/mnt/c/Users/basem/Projects/ISI/isi_darma/boteval-darma-task/data/data'
        
        # interactive_session()
        # mturk_chats = load_chats_per_id(mturk_data_dir, existing_conv['id'])
        # TODO inject mturk responses into conversation
        # breakpoint()
        interactive_session()
    
    