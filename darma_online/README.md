# DARMA ONLINE

* [Description](#description)
* [Code Structure](#code-structure)
* [Credentials and Configuration](#credentials-and-configuration)
* [Installation](#installation)
* [Usage](#usage)
* [Contact](#contact-for-support-or-contributing)

---

## Description
This directory contains the code and usage of the DARMA Online engagement software. DARMA Online identifies toxic users on Reddit and
provides alerts to moderators. The interactions of the agent with users is stored in `csv` databases. 
DARMA Online can be deployed as a docker, which allows the agent to be deployed on multiple subreddits. The agent's behavior is controlled using configuration files. 

This software is part of the DARMA project, which is a collaboration between the Information Sciences Institute and DARPA.

## Code structure
The driver code for intiating a bot instance is in `src/main.py`. The `src` directory contains the main code and the `darma_online` package. 

The `darma_online` package contains the following modules:
- `moderation_classifiers.py`
- `response_generators.py`
- `translators.py`
- `databases_manager.py`

Individual modules can be tested using test scripts in the `src/tests/` directory.

## Credentials and Configuration

The agent requires a Reddit developer's app to operate. The credentials for the account should be stored in `creds.yaml`. The format of the file is as follows:
```
username: <username>
password: <password>
client_id: <client_id>
client_secret: <client_secret>
```

Similarly, the configuration for the agent is stored in `config.yaml`. The format of the file is as follows:

```
toxicity_threshold: <floating number between 0 and 1>
use_moderator: <boolean for using the fine-tuned moderator>
data_path: <absolute path to the data folder for accessing templated responses and storing agent's interactions>
bot_responses: <absolute path to templated responses>
creds_yaml: <absolute path to credentials yaml file>
json_output_path: <absolute path to the "/data/conversations/" directory>
intersection_scores_path: <absolute path to store the moderation decision under "/data/intersection/">
```

The `main.py` script takes the path to the configuration file as an arguments:
```
--subreddit <subreddit_name> 
--passive <boolean for passive mode>
--mod_assist <boolean for using enabling alerts to moderators>
--lang <language for the subreddit. Currently supports english/french/german>
--test <boolean to run the agent in test mode>
```

Since the agent is deployed as a docker, the arguments to the `main.py` script can be modified in the `Dockerfile`. The next section discusses details about installing requirements and building the docker.

## Installation
- (optional)The required packages are listed in `requirements.txt`. The requirements can be installed using `pip install -r requirements.txt`. This step is optional since the docker will be built with the required packages.
- The docker building and running process can be exceuted using shell scripts. To make the shell scripts executable use `chmod +x <script_name>`.
- Then, the docker can be build using the shell script `build.sh`.

## Usage
Once the docker is built, it can be deployed for the specified subreddit using the `run.sh` shell script. This script takes the custom name for the deployed docker container as an argument. The script also mounts the data folder to the docker container.  
Run the docker using `run.sh <container name>`.

## Contact (for Support or Contributing)
If you have any issues running the Darma Agent, please feel free to also create an issue or contact us if you would like to contribute to the project. 
Contact: [@darpan-jain](https://www.darpanjain.com/) or [@jonmay](https://www.isi.edu/~jonmay/).

---
