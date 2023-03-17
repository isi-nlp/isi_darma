import abc

class Endpoint(metaclass=abc.ABCMeta):
    
    name = None
    
    def query(self, _input: str, *args, **kwargs) -> str:
        raise NotImplementedError
    
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'name') and
            hasattr(subclass, 'query') and 
            callable(subclass.query)
        )
