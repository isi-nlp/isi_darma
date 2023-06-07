# Adding Endpoint

## Instructions:
1. Create a new endpoint file calling it for example: `my_new_endpoint.py`.
2. Create a module called for example `MyNewEndpoint`. 
3. Make `MyNewEndpoint` Extend `Endpoint`.
4. Set `name` equal to your choice, which will be used to identify your new endpoint (following python variable name convention).
5. Optionally implement `__init__` if needed to do any one time endpoint related configs or initializations.
6. Implement `query` function of endpoint.

Finally you should have a module file that looks like the following:

```
from . import Endpoint

class MyNewEndpoint(Endpoint):

    name="MyNewEndpointArbitraryName"

    def __init__(self):
        # any necessary intializations
        pass
            
    def query(
        self,
        _instruction: str,
        turns:List[Dict], 
        turn_idx:int, 
        **kwargs
    ) -> str:
        return "i am a dummy endpoint response"
```

From the [variable/prompt definition](../prompt_generator/README.md) you can then set endpoint or default endpoint to the `name` of this endpoint to be used. No need to any additional modifcations or implementation in any other file in the project directory as all endpoints in this directory will be automatically loaded, and initialized on the runtime.

Further details and clarifications explained below.


## Endpoint Interface
### An endpoint has to extend `Endpoint` interface from [`_interface.py`](_interface.py) so that the new endpoint class follows the following:

- Have a `name` which is not `None`, used as identifier of the endpoint throughout the project so that it can be used for example in [a variable/prompt definition](../prompt_generator/README.md).
- Implement `query` function that returns a string corresponding to the outcome of the endpoint call
    ```
    def query(
        self,
        _instruction: str,
        turns:List[Dict], 
        turn_idx:int, 
        **kwargs
    ) -> str:

    ```


### How does the query function work?
The simplest way to implement a new endpoint is to overload the class and have the `query` method making an `api` call or something like calling a simple `model`.`predict` function.

However the interface exposes the endpoint definition to many `args` that can be used to create more dynamic complex endpoint calls such as including the context or optionally fixing hyperparams per different calls.

Here are explanations of the inputs of the `query` method:

- `_instruction` (`str`): a statement treated typically as an instruction to the endpoint (i.e. instruction part of a prompt of large language model), could be set None and not used if not needed (e.g. in the case of specialized non-lm classifier).


- `turns` (`List`[`Dict`]): list of dicts corresponding to all past turns of the conversation including the topic, each dict follows the following format:

    ```
    {
        "text": "The lack of respect and open-mindedness in political discussions may be due to affective polarization, the belief those with opposing views are immoral or unintelligent. Intellectual humility, the willingness to change beliefs when presented with evidence, was linked to lower affective polarization.",

        "is_seed": True, 
        
        "user_id": "Topic", 
        
        "thread_id": -1,

        "data": {
            "speaker_id": "Topic"
        }
    }
    ```

- `turn_idx` (`int`): turn number in the conversation so that it can be used (if needed) to set args possibly of actual endpoint calls.

- `**kwargs`:
    1. includes any additional arguments that are optionally defined through the [variable/prompt definition](../prompt_generator/README.md) including but not limited to api call arguments (i.e. `temperature` and `frequency_penalty` for OpenAI Completion).
    2. includes internal arguments that are defined in [prompt_generator.py](../prompt_generator/prompt_generator.py): `persona_title`
    3. includes internal arguments that are defined in [_variable.py](../prompt_generator/_variable.py): `endpoint_kwargs` mentioned in (1) and `leaf_variable` (it means not root variable but not necessarily leaf - TODO rename to internal node, or switch to root and switch logic).