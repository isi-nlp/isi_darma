import re
import logging as log
from multiprocessing import Lock, cpu_count
from multiprocessing.pool import ThreadPool
from typing import List
from ._variable import Variable, ROOT_TOKEN_REGEX

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
    - Multiple endpoints
    - Tracing of recent assignments of variable-tokens per instruction/variable
    - Turn aware variables according to frequency of assigning
    
    TODO make post-processing routines somehow (such as detecting end)

    @author: Basem Rizk
    
    """
    
    def __init__(self, config_json: dict,
                 endpoints: dict,
                 few_shot_example=None,
                 default_endpoint:str='query_lm',
                 num_threads:int=None):
        """

        Args:
            config_json (dict): JSON formatted persona configuration
            endpoints (dict): dictionary of endpoint function calls including lm call
            few_shot_example (_type_, optional): Not tested but added for backward 
            compatibility. Defaults to None.
            default_endpoint (str, optional): Name of endpoint to a lm call. Defaults 
            to 'query_lm'.
        """
                
        self.endpoints = endpoints
        self.default_endpoint = default_endpoint
        self.id = config_json['id']
        self.notes = config_json['notes']
        self.title = config_json['title']    
        self.instruction = Variable(config_json) # Similar structure to variables
        self.few_shot_example = few_shot_example     
        
        if not num_threads:
            num_threads = cpu_count()
        self.thread_pool = ThreadPool(processes=num_threads)
        self.variables = config_json.get('preprocess_variables')
        
        if self.variables:
            self.variables = {
                x['id'] : Variable(x, leaf_variable=True) 
                for x in self.variables
            }
            self.variables_master_lock = Lock()
            self.variables_locks = {
                k: Lock() for k in self.variables
            }
        
        log.info(f'Init PromptGenerator using {self.thread_pool._processes}')

    def run(self, turns: List[str], turn_idx: int) -> str:
        """

        Args:
            turns (str): concatentation of all past turns of the conversation
            turn_idx (int): turn number in the conversation used to set args of
            language model calls

        Returns:
            str: bot response given the generated/constant prompt using the default lm
        """
        
        
        self.turns = turns
        self.turn_idx = turn_idx
        
        self._decode_tokens(self.instruction)

        # self._decode_tokens(self.instruction)
        # messages = self._messages_compose()
            
        # log.debug(messages)
            
        
        kwargs = dict(self.instruction.endpoint_kwargs)
        
        if turn_idx > 0:
            # For backward compatibility with previous experiments
            kwargs.update(
                frequency_penalty=2, 
                presence_penalty=2,
                temperature=1
            )
        
        response = self._get_endpoint(self.instruction)(
            self.instruction, **kwargs
        )

        return response.strip()
    
    def _get_endpoint(self, leaf_variable):                        
        return lambda instruction, **kwargs: self.endpoints[leaf_variable.get(
            'endpoint',
            self.default_endpoint
        )](
            str(instruction),
            self.turns,
            self.turn_idx,
            **{'persona_title': self.title, **kwargs}
        )
        
        
        
    def _decode_tokens(self, variable: Variable) -> Variable:
        
        def _decode_token(token: str):
            token_split = re.findall(ROOT_TOKEN_REGEX, token)
            token_root = token_split[0]
            with self.variables_master_lock:
                variable_lock = self.variables_locks[token_root]
                
            with variable_lock:
                leaf_variable = self.variables.get(token_root)
                if not leaf_variable:
                    raise Exception(
                        f'{token_root} not defined in preprocess variables.'
                    )
                    
                if leaf_variable.is_assignable(self.turn_idx):  
                    # Need to be queried      

                    log.debug(
                        f'From {variable.get("id", "init")} '
                        f'Executig call #{leaf_variable._assign_cnt + 1} '
                        f'to obtain variable {leaf_variable["id"]}'
                    )
                    # print(
                    #     f'From {variable.get("id", "init")} '
                    #     f'Executig call #{leaf_variable._assign_cnt + 1} '
                    #     f'to obtain variable {leaf_variable["id"]}'
                    # )
                    
                    sub_instruction = str(self._decode_tokens(leaf_variable,))   
                
                    leaf_variable['response'] = self._get_endpoint(leaf_variable)(
                        sub_instruction,
                        **leaf_variable.endpoint_kwargs
                    )
                    
                    value = self.reduce(leaf_variable)
                    if value is None:
                        log.error(
                            'Multiple calls in the same turn might arise as'
                            'None reduction is observed'
                        )
                    leaf_variable.assign(
                        value,
                        turn_idx=self.turn_idx
                    )
            
            # Support other value formats such as 'value-list'
            token_format = '-'.join(token_split[1:])
            return leaf_variable, token_format
        
        tokens = variable.get_tokens()
        for token, decoding_var__format in zip(
            tokens, 
            self.thread_pool.map(_decode_token, tokens
        )):
            variable.replace(token, decoding_var__format)

        return variable
    
    def reduce(self, leaf_variable):
        reduction = leaf_variable['response']
        if leaf_variable.get('post_regex'):
            reduction = re.findall(str(self._decode_tokens(
                    Variable(
                        leaf_variable['post_regex'].lower(),
                        leaf_variable=True
                    ), 
                )),
                reduction.lower()
            )
            leaf_variable.assign(str(reduction), format='list')
        
        post_func = leaf_variable.get('post_func')
        if post_func:
            if not isinstance(post_func, list):
                post_func = [post_func]
            for func in post_func:
                reduction = eval(str(
                    self._decode_tokens(
                        Variable(func, leaf_variable=True)
                    )
                ))(reduction)
        return reduction
    

    def is_dynamic_prompt(self): 
        return not self.instruction.is_constant()
    
    def backspace(self): 
        [v.backspace() for v in self.variables.values()]
            
    def debug_prompt(self): return self.instruction.trace()

    def debug_variables(self):
        from colorama import Fore, Style
        def colored(_str, color=Fore.CYAN):
            return f'{color}{_str}{Style.RESET_ALL}'
        out = ""
        for k, v in self.variables.items():
            out += f'###### Variable({colored(k)})\n'
            out += f'### {colored("assign_cnt")}: {v._assign_cnt}\n'
            out += f'### {colored("assignments")}:\n' 
            out += "\n".join(
                [
                    f"- @{colored(k, color=Fore.BLUE)}: {colored(str(v), color=Fore.YELLOW)}" 
                    for k, v in v._assignments.items()
                ]
            ) + "\n"
            out += f'### {colored("tokens")}:\n'
            out += "\n".join(
                [
                    f"- @{colored(k, color=Fore.BLUE)}: {colored(v.get_assignment(), color=Fore.YELLOW)}" 
                    for k, v in v._variables.items()
                ]
            ) + "\n"
            out += f'### {colored("instruction-out")}: {colored(str(v), Fore.YELLOW)}\n'
            out += f'### {colored("extra parameters")}:\n'
            out += "- \n".join(
                [
                    f"- @{colored(k, color=Fore.BLUE)}: {colored(str(v), color=Fore.YELLOW)}" 
                    for k, v in v._parameters.items()
                ]
            ) + "\n\n"
        return out
    