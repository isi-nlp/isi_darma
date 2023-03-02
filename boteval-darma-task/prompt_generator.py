
import re
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool
import textwrap

PRINT_WIDTH = 150
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
        

TOKEN_REGEX = '<([\w-]+)>'
ROOT_TOKEN_REGEX = '([\w]+)'

class PromptGenerator:
    """
    A class used to adapt to dynamic formulation of persona configuration.
    Dynamic Formulation at the moment means creating embedable instruction
    prompts for a persona while the tokens are based on other pre-processing
    prompts.
    
    Features:
    - Parsing embeddable prompts
    - Post-processing prompts with post-regex, and any # of post-func (lambda functions)
    - Parsing embeddable post-regex; Saving their (TOKEN)-list variable
    - Parsing embeddable post-func
    - API agnostic

    TODO make post-processing routines somehow (such as detecting end)
    TODO allow logging of pre-processing prompts respones
    TODO instead of using pre-processing prompts, include access to other end-points
    TODO make it turn aware if needed
    
    
    @author: Basem Rizk
    
    """
    
    def __init__(self, config_json: dict,
                 query_lm,
                 few_shot_example=None):
        self.query_lm = query_lm
        self.id = config_json['id']
        self.notes = config_json['notes']
        self.title = config_json['title']    
        self.instruction = config_json['instruction']
        self.few_shot_example = few_shot_example     
           
        self.threadPool = ThreadPool()
        self.variables = config_json.get('preprocess_prompts')
        if self.variables:
            self.variables = {
                x['id'] : x for x in self.variables
            }
            self.variables_master_lock = Lock()
            self.variables_locks = {
                k: Lock() for k in self.variables
            }



    def run(self, seed_turns, turn_idx):
        prompt = self._prompt_compose(
            seed_turns, turn_idx
        )
        
        if turn_idx == 0:
            final_message_text =\
                self.query_lm(prompt, n=10)
        else:
            final_message_text =\
                self.query_lm(
                    prompt, frequency_penalty=2, 
                    presence_penalty=2,
                    temperature=1
                )
                
        return final_message_text.strip()
        
        
    def _prompt_compose(self, seed_turns, turn_idx):
        if self.few_shot_example == 'nvc':
            few_shot_example = self.get_fewshot_example(turn_idx)
        else:
            few_shot_example = ""

        instruction = self.instruction
        tokens = re.findall(TOKEN_REGEX, instruction)
        if tokens:
            instruction = self._decode_tokens(self.instruction, seed_turns)
        if few_shot_example == "":
            prompt = f'{instruction}\n\n{seed_turns}\n'
        else:
            prompt = f'{instruction}\n\n{few_shot_example}\n\n###\n\n{seed_turns}\n'

        print_wrap_text(f'Generated Instruction: {instruction}')
               
        return prompt + f'user {self.title}:'

    def _decode_tokens(self, statement, seed_turns):
        def _decode_token(token):
            token_split = re.findall(ROOT_TOKEN_REGEX, token)
            token_root = token_split[0]
            with self.variables_master_lock:
                variable_lock = self.variables_locks[token_root]
                
            with variable_lock:
                leaf_prompt = self.variables.get(token_root)
                if not leaf_prompt:
                    raise Exception(f'{token_root} not defined in preprocess prompts.')
                    
                if not leaf_prompt.get('value'):     
                    # Need to be queried      
                    leaf_prompt['response'] = self.query_lm(
                        "\n".join([
                            seed_turns, 
                            self._decode_tokens(
                                leaf_prompt['instruction'], seed_turns
                            )    
                        ]))
                    
                    leaf_prompt['value'] = self.reduce(leaf_prompt, seed_turns)
                             
            # Support other value formats such as 'value-list'
            return leaf_prompt["-".join(['value'] + token_split[1:])]
        
        tokens = re.findall(TOKEN_REGEX, statement) 
        for token, decoding in zip(tokens, self.threadPool.map(_decode_token, tokens)):
            statement = statement.replace(f'<{token}>', decoding)

        return statement
    
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
    
    
    def reduce(self, leaf_prompt, seed_turns):
        reduction = leaf_prompt['response']
        if leaf_prompt.get('post_regex'):
            reduction = re.findall(
                self._decode_tokens(
                    leaf_prompt['post_regex'].lower(), 
                    seed_turns
                ),
                reduction.lower()
            )
            leaf_prompt.update({
                'value-list': str(reduction)
            })
        
        post_func = leaf_prompt.get('post_func')
        if post_func:
            if not isinstance(post_func, list):
                post_func = [post_func]
            for func in post_func:
                reduction = eval(
                    self._decode_tokens(func, seed_turns)
                )(reduction)
        
        return reduction