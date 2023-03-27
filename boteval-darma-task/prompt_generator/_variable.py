import re
import logging as log

ROOT_TOKEN_REGEX = '([\w]+)'
TOKEN_REGEX = '<([\w-]+)>'
# Difference is TOKEN_REGEX accepts '-<SOME_FORMAT>'
# which would correspond to middle transformation of value
# such as '-list', which is list format

class Variable:
    """
    A very flexible class used to organize variable/instruction updates and easily extend to trace history or current replacements in tokens.
    """
    def __init__(self, parameters, leaf_variable=False):
        if not isinstance(parameters, dict):
            parameters = {'instruction': parameters}
        self._parameters = parameters
        self.instruction_raw = self._parameters.get('instruction')
        self.endpoint_kwargs = self._parameters.get('endpoint_kwargs', {})
        self.endpoint_kwargs.update(leaf_variable=leaf_variable)
        self._variables = {
            t: None
            for t in re.findall(TOKEN_REGEX, self.instruction_raw)
        }
        self._assign_cnt = 0
        self._assignments = {} # tracking assignments of value
        # self._look_up = self._parameters.get('look_up', None)
    

    def get_tokens(self): return self._variables.keys()
    
    def replace(self, token: str, value, format: str=None):
        """

        Args:
            token (str): token/key name pointing to  an existing value; however, if new token is given, it will still be forceably added.
            value (_type_): value of assignment/replacement
            format (str, optional): name of the format of the type of value; if not provided then assignment refers to original format of the value. Defaults to None. Defaults to None.
        """
        if format:
            token = f'{token}-{format}'
        self._variables[token] = value
    
    def get(self, name:str, default:str=None):
        return self._parameters.get(name, default)
    
    def __getitem__(self, name: str): return self.get(name)
    
    def __setitem__(self, name: str, val): self._parameters[name] = val
    
    def update(self, _dict: dict): self._parameters.update(_dict)
    
    def get_assignment(self, format: str=None):
        """

        Args:
            format (str, optional): name of the format of the type of value; if not provided then assignment refers to original format of the value. Defaults to None. Defaults to None.

        Returns:
            any: value of assignment
        """
        key = 'value'
        if format:
            key = f'{key}-{format}' 
        return self._parameters[key]
        
    def trace(self) -> str:
        """

        Returns:
            str: debug of insturction with colored format to be printed in console, including assignment count and value of assignment between square brackets inline.
        """
        statement = self.instruction_raw
        decoding_placeholder =\
            "[\033[95m{cnt}\033[00m : \033[96m{decoding}\033[00m]"
        for token, (var, format) in self._variables.items():
            statement = statement.replace(
                f'<{token}>', 
                decoding_placeholder.format(
                    cnt=var._assign_cnt,
                    decoding=var.get_assignment(format=format) 
                )
            )
        return statement

    def __str__(self) -> str:
        statement = self.instruction_raw
        for token, (var, format_) in self._variables.items():
            decoding = var.get_assignment(format=format_)
            statement = statement.replace(
                f'<{token}>', decoding
            )
        return statement

    def is_assignable(self, turn_idx:int) -> bool:
        """
        Args:
            turn_idx (int): globally defined value representing the current turn of the conversation

        Returns:
            bool: indicator whether the variable value can be assigned at current turn or not.
        """
        if self.get('value') is None:
            return True
        if self._assignments.get(turn_idx) is not None:
            return False
        freq = self.get('frequency', turn_idx + 2)
        return ((turn_idx + 1) % freq) == 0
    
    def assign(self, value, turn_idx: int=None, format:str=None):
        """

        Args:
            value (any): value to be assigned
            turn_idx (int, optional): globally defined value representing the current turn of the conversation. requried if arg `format` is not provided Defaults to None.
            format (str, optional): name of the format of the type of value to be assigned; if not provided then assignment refers to original format of the value. Defaults to None.
        """
        if format is not None:
            key = f'value-{format}'
        else:
            # print(f"token [{self.get('id')}] = [{self.get('value') is not None}]")
            key = 'value'
            self._assign_cnt += 1
            self._assignments[turn_idx] = value
        self._parameters[key] = value

        if not value:
            log.error(
                f'Empty Assignment @ => #{self._assign_cnt}: '
                f'{key}({self.get("id")}) = {value}'
            )
        else:
            log.debug(
                f'Assignment #{self._assign_cnt}: '
                f'{key}({self.get("id")}) = {value}'
            )
        
    def backspace(self): 
        """
        Goes back in time one step
        """
        if self._assignments.get(self._assign_cnt):
            self._assignments.__delitem__(self._assign_cnt)
        self._assign_cnt -= 1
        
    def is_constant(self): return not self._variables
