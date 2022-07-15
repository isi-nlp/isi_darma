# DARMA Model Chat

## Overview

Main command: `python -m darma_chat`
This is equivalent to `python -m darma_chat conf=darma`, which will run crowdsourcing tasks on the local server. Use `python -m darma_chat conf=mturk_sandbox` to run the tasks on a heroku server that was set up with https://mephisto.ai/docs/guides/quickstart/ and publish them on Mechanical Turk. 

This task is adapted from `https://github.com/isi-nlp/ParlAI/tree/main/parlai/crowdsourcing/tasks/model_chat` and therefore there may be a number of unnecessary artifacts from this task that remain in this script.

## Contributing: Setup and Quick Start

1. Set up environment: `conda create -n darma python=3.8`; `conda activate darma`
1. clone this source code and cd into the root of the repo
1. Run `pip install -e .`
    > This installs  mephisto, parlai etc

1. check either of `darma_chat -h` or `python -m darma_chat -h` works. If they dont work, the previous step has failed, go and fix it

1. Configure Mephisto
    ```bash
    MEPHISTO_DATA=$HOME/mephisto-data
    mkdir -p $MEPHISTO_DATA
    mephisto config core.main_data_directory $MEPHISTO_DATA
    mephisto check
    ```

1. Run darma_chat  
 We have two options:
    1. Locally:  
       Either `darma-chat conf=darma`
       or  
        simply `darma-chat`
    2. Remotely on mturk with heroku  
      More info is here https://mephisto.ai/docs/guides/quickstart/
          1. Configure AWS credentials for mturk
              ```bash
              mephisto register mturk \
                  name=my_mturk_user \
                  access_key_id=$ACCESS_KEY\
                  secret_access_key=$SECRET_KEY
              #AWS credentials successfully saved in ~/.aws/credentials file.
              ```
          1.  Configure heroku
              ```bash
              npm install -g heroku
              heroku login -i  # requires heroku login
              python -m mephisto.scripts.heroku.initialize_heroku
              ```
          1. Run darma chat
               ```bash
               darma-chat conf=mturk_sandbox
              ```

Issue tracking: https://github.com/isi-nlp/isi_darma/issues 


### Docker deployment
1. cd to the root of this repo
1. `docker build . -f dockers/Dockerfile -t darma_chat:v0.1`

---

## General tips 

If you don't know where to start, run the baseline example with `python run.py conf=example` and see in the terminal all the parameters that were used for this run. Most of these parameters are well-explained in `model_chat_blueprint.py`. 



### Frontend Customizations

Here, we map frontend customizations and the corresponding scripts that need to be modified. 
- Main script that contains all the components: `frontend/components/chat_app_with_onboarding.jsx`
- Onboarding task (informed consent form): 
  - Informed consent form content: `frontend/components/onboarding_components.jsx` under `<OnboardingDirections>`
  - Update configuration in `darma.yaml`
    - onboard_task_data_path: `${task_dir}/task_config/darma_onboard_task_data.json`
    - annotations_config_path:`${task_dir}/task_config/darma_annotations_config.json`
  - Inputs (radio input and text input): 
    - modify frontend: `frontend/components/inputs.jsx`
    - Answer choices: `task_config/darma_annotations_config.json`
- Main task 
  - left pane instructions: 
    - `task_config/darma_task_description.html`
  - task description: 
    - `task_config/darma_left_pane_text.html`
  - title: 
    - simply update `task_title` in `darma.yaml`
  - message box: `frontend/components/message.jsx`
  - Post-conversation survey: 
    - Selection choices: 
      - `parlai/crowdsourcing/tasks/darma_chat/frontend/components/response_panes.jsx` under `function RatingSelector`
    - Survey questions: 
      - set `final_rating_question` with your question. For multiple questions, separate them by "|" in a single string. 



## Seed conversation customizations 

- By setting `conversation_start_mode: custom` in `darma.yaml` and specifying the path to a json file with `seed_conversation_source`, we load a json file that contain dialogues that can seed conversations for evaluation. 
- modify the `_run_initial_turn` for `ModelChatWorld`  in `worlds.py` to load dialogue data and establish it as the starting point. 

## Model customization

- Specify the model to chat with in `task_config/darma_model_opts`
  - choose either a model that is hosted by ParlAI (list can be found [here](https://parl.ai/docs/zoo.html)) or provide a path to a model that has been trained locally with ParlAI. 

- Model conversation logic can be modified in the `ModelChatWorld` class inside `worlds.py` 
  - Conversation context: 
    -  `DarmaContextGenerator` inside `utils.py` is responsible for loading the seed conversation data (context info), which is supplied to the `_run_initial_turn()` method. 
    -  A static variable keeps track of the index. 
    -  Currently, only one assignment is created for a single conversation seed.  

## Enabling MT

> see `translator.py` for the code

Add this config block as `mephisto.blueprint.translator`

```yaml
translator:
  activation: 'pre' # pre, post, pre+post, null
  preprocess: rtg_api
  preprocess_args:
    # TODO: change the URL to DARMA hosted service
    api_url: http://rtg.isi.edu/many-eng/v1/translate
  postprocess: huggingface
  postprocess_args:
    model: Helsinki-NLP/opus-mt-en-fr
```
The key `activation` takes the following values 
* `pre` - Only translate human input (via `preprocess` config)
* `post` - Only translate bot output (via `postprocess` config)
* `pre+post` - Enable both `pre` and `post` 
* `null` - Disable MT. Which has same effect as deleting the whole `translator` config block

`preprocess` and `postprocess` takes the MT backend __name__.
Whereas `{pre,post}process_args` take a dictionary of arguments to MT backend.

__The following MT backends are supported__
* `rtg_api` which calls RTG over a REST API. See http://rtg.isi.edu/many-eng/ 
* `huggingface` calls `transformers` library. Requires `model` argument which can be obtained from https://huggingface.co/models?pipeline_tag=translation




## Debug logs/tips 

- Q: I'm making changes to the front end and it seems like they are not reflected in my task. 
  - A: examine the config that gets printed when running `python run.py` and make sure that all configurations point to the directory that you're making changes to. The `get_task_path()` function and imports that have not been updated after copying files from another crowdsourcing task directory may be the culprit. 
- To use custom opts (configs) in `worlds.py`, make sure to add them to the blueprint arguments, and then add them where `shared_state.world_opt.update` is called. 
-  If you get an error `error: src refspec master does not match any` 
it possibly because you have changed default branch as something other than `master`
So here is how to set the default as master:
  `git config --global init.defaultBranch master`