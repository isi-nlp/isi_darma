import re
from boteval import log

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
            parameters = {'id': '_root', 'instruction': parameters}
        self._parameters = parameters
        self._instruction_raw = self._process_raw_instructions(
            self._parameters.get('instruction')
        )
        self._recent_turn = 0

        self.endpoint_kwargs = self._parameters.get('endpoint_kwargs', {})
        self.endpoint_kwargs.update(leaf_variable=leaf_variable)
        self._variables = {
            t: None
            for statement, _ in self._instruction_raw
            for t in re.findall(TOKEN_REGEX, statement)
        }
        self._assign_cnt = 0
        self._assignments = {} # tracking assignments of value
        # self._look_up = self._parameters.get('look_up', None)
    
    def update_turn(self, turn_idx):
        self._recent_turn = turn_idx
        
    def _process_raw_instructions(self, instruction_raw) -> list(tuple([str, int])):
        """Processes input of instruction and returns appropriately formated instruction_raw instance of statement and offsets pairs.

        Args:
            instruction_raw (any): Can be a single statement of a list of tuples of (str, int) corresponding to statement of instruction and offset of turn index.

        Raises:
            RuntimeError: Error of parsing instruction due to possible format problem

        Returns:
            list(tuple([str, int])): list of tuples of two elements, the first corresponding to statement and the second correspoding to offset of turn index
        """
        if not isinstance(instruction_raw, list):
            instruction_raw = [(instruction_raw, 0)]

        try:
            offsets = []
            for statement, offset in instruction_raw:
                assert isinstance(statement, str)
                assert not offset or offset > 0
                offsets.append(offset)
            assert len(set(offsets)) == len(offsets)
        except:
            raise RuntimeError(
                'Error parsing instruction, please ensure correct format'
                f'of variable with id: ({self._parameters["id"]})'
            )
        return sorted(instruction_raw, key = lambda x: x[1])
    
    def get_curr_instruction_statement(self, turn_idx:int) -> str:
        """Returns current instruction statement per the given turn_idx

        Args:
            turn_idx (int): 0-indexed, turn index of the conversation

        Returns:
            str: current instruction per the given index
        """
        self._recent_turn = turn_idx
        for statement, offset in reversed(self._instruction_raw):
            if turn_idx >= offset:
                return statement
        log.critical(
            f'Your defintion of the instruction: \n"{statement}"\n'
            f'considering offset of value "{offset}" might be wrong!'
        )
        return statement
    
    def _set_curr_instruction_statement(self, updated_statement, turn_idx:int) -> None:
        """Only meant for hacky behaviors and debugging; sets value to current instruction assignment given turn_idx
        Args:
            updated_statement (str): updated statement of instruction with offset beyond or equal to turn_idx
            turn_idx (int): 0-indexed, turn index of the conversation.

        """
        self._recent_turn = turn_idx
        for i, (statement, offset) in enumerate(reversed(self._instruction_raw)):
            if turn_idx >= offset:
                self._instruction_raw[-i] = updated_statement
                return
            
        log.critical(
            f'Issue setting the value of instruction statement'
            f'Your defintion of the instruction: \n"{statement}"\n'
            f'considering offset of value "{offset}" might be wrong!'
        )
    
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
        
    def trace(self, turn_idx:int=None) -> str:
        """

        Returns:
            str: debug of insturction with colored format to be printed in console, including assignment count and value of assignment between square brackets inline.
        """
        if turn_idx:
            self._recent_turn = turn_idx
        statement: str = self.get_curr_instruction_statement(self._recent_turn)
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
        statement: str = self.get_curr_instruction_statement(self._recent_turn)
        for token, (var, format_) in self._variables.items():
            decoding = var.get_assignment(format=format_)
            statement = statement.replace(
                f'<{token}>', decoding
            )
        return statement

    def is_assignable(self, turn_idx:int) -> bool:
        """
        Args:
            turn_idx (int): 0-indexed, globally defined value representing the current turn of the conversation

        Returns:
            bool: indicator whether the variable value can be assigned at current turn or not.
        """
        self._recent_turn = turn_idx
        if self.get('value') is None:
            return True
        if self._assignments.get(turn_idx) is not None:
            return False
        freq = self.get('frequency', turn_idx + 2)
        
        # TODO allow frequency None to still set up all statements in instruction_raw if more than one
        return ((turn_idx + 1) % freq) == 0
    
    def assign(self, value, turn_idx: int=None, format:str=None):
        """

        Args:
            value (any): value to be assigned
            turn_idx (int, optional): 0-indexed, globally defined value representing the current turn of the conversation. requried if arg `format` is not provided Defaults to None.
            format (str, optional): name of the format of the type of value to be assigned; if not provided then assignment refers to original format of the value. Defaults to None.
        """
        self._recent_turn = turn_idx
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
        
    def backspace(self, turn_idx): 
        """
        Goes back in time one step
        """
        ass_ptrs = list(self._assignments.keys())
        if len(ass_ptrs) and max(ass_ptrs) > turn_idx:
            if self._assignments.get(self._assign_cnt):
                self._assignments.__delitem__(self._assign_cnt)
            self._assign_cnt -= 1
        
    def is_constant(self): return not self._variables and len(self._instruction_raw) <= 1
