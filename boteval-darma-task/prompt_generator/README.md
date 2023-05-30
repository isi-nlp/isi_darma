# Designing Dynamic Prompts 


## Prompt Definition
### A prompt at least is defined by `title`, `instruction` and `id` for organization purposes:
```
    {
        "default_endpoint": "gpt3",
        
        "id": "wisebeing-gpt3",
        
        "notes": "baseline", 
        
        "title": "wisebeing",

        "instruction": "The following is a conversation with a wise and loving being who has an understanding of how nonviolent communication work. This being is dedicated to building a more civil online environment."
    }
```

Where `title` corresponds to the title of the bot. It gets typically (Defined by the endpoint itself) appended to the final constructed prompt before calling the `default_endpoint` as follows:

>
> `<instruction>`
>
> `<context>`
>
> `<title>`:
>

Additionally other supported arguments can be included in the Prompt definition such as:

- `default_endpoint` (`string`) : choice of default endpoint (has to be a lanugage model) overriding the default endpoint if any passed to boteval.
- `endpoint_kwargs` (`json`/`dict`): keyword arguments dependend on the endpoint
    > Example with args of OpenAI GPT3/ChatGPT:
    > ```
    > "endpoint_kwargs": {
    >     "n": 10,
    >     "temperature": 0.5
    > },
    
- `author` (`string`): used only for tracing and debugging purposes.
- `notes` (`string`): used only for tracing and debugging purposes. 
- `preprocess_variables` (`list`(`json`/`dict`)): plugged-in/chained variable definitions if any variables were defined in the instruction. (*Explained below*)


## Dynamic Prompts:
### The key difference between a static prompt (i.e. the one above) and dynamic prompt is plugging variables (between `<` and`>`), where the instruction would look something like that: 
```
"instruction": You are an intelligence moderator agent. `<to_be_moderated_users>` are to be moderated in the following conversation because `<moderation_reasoning>`.
```
These variables (i.e `to_be_moderated_users` and `moderation reasoning`) should be defined in the prompt definition as `preprocess_variables`. Accordingly their will be reduced in the runtime to their values according to each of their definitions, and replace the token in the `instruction` template above.


## Preprocess Variables Defintion:
### A preprocess variables which is an essential part of defining a Dynamic Prompt consists of at least `id` and `instruction`.

```
"preprocess_variables" = [
    {
        "id": "to_be_moderated_users",
        
        "instruction": "For each user, classify using Yes or No if the user need moderation based on their responses in the conversation: (Format your response as 'User user_name: no/yes' per each user_name)",
        
        "post_regex": "(User \\w+): Yes",
        
        "regex_validation": "https://regex101.com/r/Gn1dyY/1",
        
        "post_func": "lambda x: ' and '.join(x)",
        
        "frequency": 1,

        "endpoint": "gpt3",
        
        "endpoint_kwargs": {
            "role": "system"
        }
    },
]
```
Given the defintion of this variable `to_be_moderated_users`, these arguments will passed to an endpoint (e.g `gpt3`) along with the conversation `context` to be reduced to a value that would replace its token in the prompt template.

In this particular sample variable there are few other supported optional arguments that are being used such as `post_regex`, `post_func`, `frequency`, `endpoint`, and `endpoint_kwargs` and there are more that are supported and can be included. Here is a list of some of which:

- `endpoint` (`string`) : choice of default endpoint (has to be a lanugage model) overriding the default_endpoint defined earlier (of the whole dynamic prompt).

- `endpoint_kwargs` (`json`/`dict`): keyword arguments dependend on the endpoint.
    > Example with args of OpenAI ChatGPT:
    > ```
    > "endpoint_kwargs": {
    >     "role": "system"
    > },

    `"role"` here corresponds to ChatGPT argument where `system` would typically should be used with these `variables` if one decides to use ChatGPT as endpoint for them.

    
- `frequency` (`int`): frequency of reassigning the variable (updating its value). Default is `0` meaning assigned only once on the first call. `1` meaning called every single turn. `2` meaning every other turn, and so on.

- `post_regex` (`str`): Regex for postprocessing of the raw value of a variable coming directly from the endpoint to extract elements. Returning accordingly a list that can be used plugged in prompt as other variables, and be called `<VARIABLE_NAME-list>`.

- `regex_validation` (`str`): link pointing to sample example of the regex defined being used. only used for debugging purposes.

- `post_func` (`str` or `list`(`str`)): `lambda` function or list of `lambda` functions given as `string`s to define transformations over the list retrieved by applying the `post_regex` or the value directly coming from the `endpoint` if `post_regex` is not present.


*Note that a `variable` can be a template on its own other variables defined in the list can be plugged into it.*


## Further Notes:

- Note that `endpoint_kwargs` is not limited to the defined arguments by the endpoint (i.e emotion classifier, or gpt3-lm, etc.) call used, but can be extended seamlessly based on the definition of your created endpoint modules [a relative link](../endpoints/README.md) in your project structure.

Examples from defined `GPT3` endpoint:
1. `"look_up"`: `-5`
> Used to slice the context before constructing the prompt to be fed to GPT3 auto-regressive model.
 
2. `"exclude_topic"`: `true`
> By default the GPT3 endpoint defined in this project *skips* the topic (i.e the item at the first index) from the context, as it was shown to perform much better this way.
> This argument however can be defined and implemented in the project structure easily to allow both options. 
> This argument is supported in ChatGPT, and on the contrary is `false` by default.

3. `"instruction_first"`: `true`
> If set to `true`, the constructed prompt would be in this order:
> `<instruction>` \n `<context>` instead of `<context>` `<instruction>`
> It is set to `false` by default for any `variable` in `preprocess_variables` for GPT3 endpoint defined in this project.
> This argument is *not* supported in ChatGPT, and by default the behavior is the opposite: instruction first.
