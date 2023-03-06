
import re
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool


TOKEN_REGEX = '<([\w-]+)>'
ROOT_TOKEN_REGEX = '([\w]+)'
class Variable: pass # Implemented Below


class Variable:
    """
    A class used to organize variable/instruction updates and easily extend to
    trace history or current replacements in tokens.
    """
    def __init__(self, parameters):
        if not isinstance(parameters, dict):
            parameters = {"instruction": parameters}
        self.parameters = parameters
        self.instruction_raw = self.parameters.get('instruction')
        self.variables = {
            t: None
            for t in re.findall(TOKEN_REGEX, self.instruction_raw)
        }
    
    def get_tokens(self):
        return self.variables.keys()
    
    def replace(self, token, value) -> Variable:
        self.variables[token] = value
        return self
    
    def get(self, name:str, default:str=None):
        return self.parameters.get(name, default)
    
    def __getitem__(self, name: str):
        return self.get(name)
    
    def __setitem__(self, name: str, val):
        self.parameters[name] = val
    
    def update(self, _dict: dict):
        self.parameters.update(_dict)
    
    def trace(self, debug=True):
        statement = self.instruction_raw
        if debug:
            decoding_placeholder = '\033[96m{decoding}\033[00m'
        else:
            decoding_placeholder = '{decoding}'
        for token, decoding in self.variables.items():
            statement = statement.replace(
                f'<{token}>',
                decoding_placeholder.format(decoding=decoding)
            )
        return statement
    
    def __str__(self):
        return self.trace(debug=False)
    
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

    TODO make post-processing routines somehow (such as detecting end)
    TODO make it turn aware if needed (frequency)


    @author: Basem Rizk
    
    """
    
    def __init__(self, config_json: dict,
                 endpoints: dict,
                 few_shot_example=None,
                 default_endpoint='query_lm'):
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
        self.instruction = Variable({
            "instruction": config_json['instruction']
        })
        self.few_shot_example = few_shot_example     
        
        self.threadPool = ThreadPool()
        self.variables = config_json.get('preprocess_variables')
        if self.variables:
            self.variables = {
                x['id'] : Variable(x) for x in self.variables
            }
            self.variables_master_lock = Lock()
            self.variables_locks = {
                k: Lock() for k in self.variables
            }

    def run(self, seed_turns: str, turn_idx: int) -> str:
        """

        Args:
            seed_turns (str): concatentation of all past turns of the conversation
            turn_idx (int): turn number in the conversation used to set args of
            language model calls

        Returns:
            str: bot response given the generated/constant prompt using the default lm
        """
        prompt = self._prompt_compose(
            seed_turns, turn_idx
        )
        
        if turn_idx == 0:
            response =\
                self.endpoints[self.default_endpoint](prompt, n=10)
        else:
            response =\
                self.endpoints[self.default_endpoint](
                    prompt, frequency_penalty=2, 
                    presence_penalty=2,
                    temperature=1
                )
                
        return response.strip()
        
        
    def _prompt_compose(self, seed_turns: str, turn_idx: int) -> str:
        """

        Args:
            seed_turns (str): concatentation of all past turns of the conversation
            turn_idx (int): turn number in the conversation used to set args of
            language model calls

        Returns:
            str: Prepared and generated/constant prompt appended to seed_turns and 
            properly to feed for completion llm call.
        """
        if self.few_shot_example == 'nvc':
            few_shot_example = self.get_fewshot_example(turn_idx)
        else:
            few_shot_example = ""

        # tokens = re.findall(TOKEN_REGEX, self.instruction_out)
        # if tokens:
        self._decode_tokens(self.instruction, seed_turns)
        if few_shot_example == "":
            prompt = f'{self.instruction}\n\n{seed_turns}\n'
        else:
            prompt = f'{self.instruction}\n\n{few_shot_example}\n\n' +\
                f'###\n\n{seed_turns}\n'
        
        return prompt + f'user {self.title}:'
    
    def _decode_tokens(self, variable, seed_turns: str) -> Variable:
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
                    
                if not leaf_variable.get('value'):     
                    # Need to be queried      
                    leaf_variable['response'] =\
                        self.endpoints[
                            leaf_variable.get(
                                'endpoint',
                                self.default_endpoint
                            )
                        ](
                        "\n".join([
                            seed_turns, 
                            str(
                                self._decode_tokens(
                                    leaf_variable, 
                                    seed_turns
                                ) 
                            )   
                        ]))
                    
                    leaf_variable['value'] =\
                        self.reduce(leaf_variable, seed_turns)
                             
            # Support other value formats such as 'value-list'
            return leaf_variable["-".join(['value'] + token_split[1:])]
        
        if not isinstance(variable, Variable):
            breakpoint()
        tokens = variable.get_tokens()
        for token, decoding in zip(tokens, self.threadPool.map(_decode_token, tokens)):
            variable.replace(token, decoding)

        return variable
    
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
    
    
    def reduce(self, leaf_variable, seed_turns):
        reduction = leaf_variable['response']
        if leaf_variable.get('post_regex'):
            reduction = re.findall(
                str(self._decode_tokens(
                    Variable(leaf_variable['post_regex'].lower()), 
                    seed_turns
                )),
                reduction.lower()
            )
            leaf_variable.update({
                'value-list': str(reduction)
            })
        
        post_func = leaf_variable.get('post_func')
        if post_func:
            if not isinstance(post_func, list):
                post_func = [post_func]
            for func in post_func:
                reduction = eval(str(
                    self._decode_tokens(
                        Variable(func),
                        seed_turns
                    )
                ))(reduction)
        
        return reduction
    
    def debug_prompt(self):
        return self.instruction.trace()

    def is_dynamic_prompt(self):
        if self.instruction.variables:
            return True
        return False