""" 
TODO: Still under construction
A script meant for interactive analysis and automated processes for fast experiments

@author: Basem Rizk

"""

import os, argparse
import re, json, textwrap
import logging as log
import numpy as np
from bots import GPTBot
from tabulate import tabulate
from multiprocessing.pool import ThreadPool


PRINT_WIDTH=-1 # Modified by argparse
BOT_SPEAKER_ID_REGEX = 'bot\\d+'
EXPERIMENT_OPTS_REGEX = '\\\(\w+)(\\\((\w+)\\\))?'

class MixedBots:
    
    def __init__(self, personas, engine, max_ctx_len,
                 print_width=100):
        # personas = [(<id>, <title>, <instruction>), ..]
        self.personas = personas
        self.ids = []
        self.titles = []
        for p in personas:
            self.ids.append(p[0])
            self.titles.append(p[1])
            
        self.bots = [
            GPTBot(
                engine=engine,
                persona_id=persona_id,
                # few_shot_example=existing_conv,
                max_ctx_len=max_ctx_len,
            )
            for persona_id, _, _ in self.personas
        ]
        self.print_width = print_width
        self.sub_width =\
            int((self.print_width-1)/len(self.personas))
        
        self.threadPool = ThreadPool()

        
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
        return self.threadPool.map(func, self.bots)
            
    def hear(self, msg):     
        self._iterate(lambda x: x.hear(msg))       
    
    def feed(self, txt):     
        self._iterate(lambda x: x.feed(txt))     
          
    def talk(self, verbose=2): 
        def get_gen_instruction(bot):
            reply = {"text": "Constant"}
            if bot.prompt_generator.is_dynamic_prompt():
                reply['text'] = f'{bot.prompt_generator.debug_prompt()}'
            return reply
        
        replies = self._iterate(
            lambda x: x.talk()
        )
            
        if verbose:
            self._print_responses(replies)
            gen_prompts = self._iterate(lambda x: get_gen_instruction(x))
            if verbose >= 2:
                self._print_responses(
                    gen_prompts,
                    title_placeholder="{} given the generated instruction:\n"
                )
        return replies
    
    def force_completion(self, verbose=True):
        replies = self._iterate(lambda x: x.force_completion())
        if verbose:
            table = self.fill_table([
                textwrap.wrap(
                    f'{x["text"]}',
                    width=self.sub_width
                ) for x in replies
            ])
            self._print_responses(
                table,
                title_placeholder='Completion at {}:\n',
                wrapped=True
            )
        return replies
    
    def view_seed(self):
        def get_seed(b):
            return {
                'text': b.get_seed_turns()
            }
        print('Seeds')
        seeds = self._iterate(get_seed)
        self._print_responses(
            seeds,
            title_placeholder='Seed of {}:\n',
        )
    
    def _print_responses(
        self, responses, title_placeholder='User {}:',
        wrapped=False
    ):
        if not wrapped:
            out_texts = [
                f'{title_placeholder.format(title)} {response["text"]}'
                for title, response in zip(self.titles, responses)
            ]
            table = self.fill_table([
                sum([
                    textwrap.wrap(
                        line,
                        width=self.sub_width,
                    )
                    for line in text.split('\n')
                ], [])
                for text in out_texts
            ])
        else:
            table = responses
        table = np.vstack([
            self.ids,
            table.T
        ]) 
        print(tabulate(table, headers="firstrow"))
        print('='*self.print_width)
    
    def backspace(self, verbose=True):
        removes = self._iterate(lambda x: x.backspace())
        return removes
            
    def view_variables(self, var_name=None):
        print('Variables:')
        def get_variables_desc(bot: GPTBot, ):
            desc = 'Empty due to Constant Prompt'
            if bot.prompt_generator.is_dynamic_prompt():
                desc = bot.prompt_generator.debug_variables()
                desc = desc.get(var_name) if var_name else desc
            return {"text": desc}
        descs = self._iterate(lambda x: get_variables_desc(x))        
        self._print_responses(descs, title_placeholder='Variables of {}:\n')
    
    def get_turn_idx(self):
        return self.bots[0].turn_idx               
    
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
        return x in range(0, len(alist))
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
            if is_break_query():
                break
            print('Please enter appropriate value.')    
            
    return list(map(alist.__getitem__, nums))

def load_persona_confs(confs_filename='persona_configs.json'):
    try:
        with open(confs_filename) as f:
            confs_json = json.load(f)
            # json_formatted_str = json.dumps(conf_json, indent=2)
            # print(json_formatted_str)
            for i, conf in enumerate(confs_json):
                print("="*PRINT_WIDTH)
                print(f'# {i+1} :: id({conf["id"]})')
                print(f'# Notes: {conf["notes"]}')
                print(f'# Title: {conf["title"]}')
                print('# Instruction:')
                print_wrap_text(conf['instruction'])
                print("="*PRINT_WIDTH)
    except:
        raise Exception(f"{confs_filename} properly not a proper Json formatted file")
        
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
        str([f'#{i+1}: {c["id"]}' for i, c in enumerate(convs_json)]),
        print_border=True,
        title='Conversation IDs',
    )
    
    if conv_id:
        conv = [
            c for c in convs_json
            if c['id'] == conv_id
        ][0]
    else:
        conv = pick_valid_choice(convs_json, statement='Enter # of conv: ')[0]
                
    print(f'Conversation ID: {conv["id"]}')
    print(f'Conversation Name: {conv["name"]}')
    
    return conv

def interactive_session(
        conv_file, 
        conv_id,
        engine='text-davinci-003',
        max_ctx_len=2048,
        feed_history=False
    ):
    
    
    while(True):
        existing_conv = load_conversation(filepath=conv_file, conv_id=conv_id)
        
        if feed_history:
            mturk_chats = load_mturk_chats_per_id(mturk_data_dir, existing_conv['id'])
        
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
        users_list = set()
        print('='*PRINT_WIDTH)
        for msg in existing_conv['conversation']:
            bots.hear(msg)
            users_list.add(msg["speaker_id"])
            print_wrap_text(f'User {msg["speaker_id"]}: {msg["text"]}')
            final_user = msg['speaker_id']
            print('='*PRINT_WIDTH)
        replies = bots.talk()
    
        def backspace():
            print('Removing context:')
            print(bots.backspace())

        def retry():
            bots.backspace()
            bots.talk()
            
        def respond_with_mturk_history():
            choice_idx = np.random.choice(np.arange(len(mturk_chats)))
            line = mturk_chats[choice_idx][bots.get_turn_idx()]['text']
            print_wrap_text(f'[User {final_user}]: {line}')
            continue_conversation(line)
                
        options = {
            "view_seed": lambda _: bots.view_seed(),
            "backspace": lambda _: backspace(),
            "retry": lambda _: retry(),
            "view_variables": lambda var_name: bots.view_variables(var_name=var_name),
            "view_turn": lambda _: print(f'This turn is {bots.get_turn()}') ,
            'send_mturk_res': lambda _: respond_with_mturk_history(),
        }
        
        def initiate_force_feeding(line):
            feed = line[2:]
            feeding_text = True
            if feed.endswith("\\\\"):
                feeding_text = False
                feed = feed[:-2]
            else:
                print("Enter '\\\\' to end feed.")
                
            while feeding_text:
                feed += '\n' + input()
                if feed.endswith("\\\\"):
                    feeding_text = False
                    feed = feed[:-2]
                    break
            print(f'(Feeding text):\n{feed}')
            bots.feed(feed)
            print('='*PRINT_WIDTH)
            bots.force_completion()
            
        def continue_conversation(line):
            bots.hear({
                    'speaker_id': final_user,
                    'text': line
                })
            print('='*PRINT_WIDTH)
            _ = bots.talk()
                
        
        while True:
            print('='*PRINT_WIDTH)
            line = input(f'[User {final_user}]: ')
            line = line.strip()
            if not line:
                continue
            if line == "exit":
                break
   
            if line.startswith("\\\\"):
                initiate_force_feeding(line)
            elif match := re.match(EXPERIMENT_OPTS_REGEX, line):
                groups = match.groups()
                options.get(
                    groups[0],
                    lambda _: print('This option is not defined (NOT LLM ANSWER); Try again.\n')
                )(groups[2])
            else:
                continue_conversation(line)
                
        if is_break_query():
            break

def is_break_query(quit_statement='Quitting'):
    query = input('Do you want to continue? ')
    if query.lower() in ['q', 'quit']:
        print(quit_statement)
        return True
    return False

def load_mturk_chats_per_id(chat_dir, conv_id, n=3, drop_org_text=True, drop_bot_res=True):
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

                if not drop_org_text or not org_text:
                    if not drop_bot_res or not re.match(BOT_SPEAKER_ID_REGEX, speaker_id):
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
    parser.add_argument('-conv_id',  default=None, type=str,
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
            log.getLogger().setLevel(log.CRITICAL)
    # log.getLogger().setLevel(log.DEBUG)

    if args.inter:
        mturk_data_dir = '/mnt/c/Users/basem/Projects/ISI/isi_darma/boteval-darma-task/data/data'
        
        # interactive_session()
        # TODO inject mturk responses into conversation
        # breakpoint()

        interactive_session(
            conv_file=args.conv_file, 
            conv_id=args.conv_id,
            feed_history=True
        )

    
