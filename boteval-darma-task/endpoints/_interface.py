import abc
from typing import Union, List, Dict

class Endpoint(metaclass=abc.ABCMeta):
    
    name = None
    
    def query(self, _instruction: str, turns:List[Dict], turn_idx:int, **kwargs) -> str:
        """

        Args:
            _instruction (str): a statement treated typically as an instruction to the endpoint (i.e. instruction part of a prompt of large language model), could be set None and not used if not needed (e.g. in the case of specialized non-lm classifier).
            turns (List[dict]): list of dicts corresponding to all past turns of the conversation including the topic. 
            turn_idx (int): turn number in the conversation so that it can be used (if needed) to set args possibly of actual endpoint calls.

        Raises:
            NotImplementedError: this function has to be overloaded in new endpoints.

        Returns:
            str: outcome of the endpoint call process
        """
        raise NotImplementedError
    
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'name') and
            hasattr(subclass, 'query') and 
            callable(subclass.query)
        )




    ################################################################
    # AUXILIARY FUNCTIONS
    ################################################################
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