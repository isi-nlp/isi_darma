# Chat Admin

This project offers a web interface to admnister darma chats

## Setup

```bash
git clone  https://github.com/isi-nlp/isi_darma
cd isi_darma/chat_admin
pip install -e .

python -m chat_admin -h
```

## Start Server

### Development mode

```bash

# add -d for debug
python -m path-to-config.yml -d 
```

# Deployment
```bash
python -m path-to-config.yml
```

This starts a service on http://localhost:6060 by default.


## Config file

Here is an example
```yaml
chat_dir: ../darma_chat/darma_chat/model_chat
mturk:
  sandbox: true
  endpoint_url: https://mturk-requester-sandbox.us-east-1.amazonaws.com
  profile: default    # the [default] profile in ~/.aws/credentials file
```

* `chat_dir` -- path to directory having JSON files stored by Mephisto.
* If `sandbox` is set to `true`, `endpoint_url` will be used otherwise default url is picked up by aws client.
* `profile` value is the name of credential profile in `~/.aws/credentials` to use.



**CLI options:**

```
$ python -m chat_admin -h
usage: chat-admin [-h] [-d] [-p PORT] [-ho HOST] [-b BASE] config

Deploy a chat admin UI

positional arguments:
  config                Path to config file

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Run Flask server in debug mode (default: False)
  -p PORT, --port PORT  port to run server on (default: 6060)
  -ho HOST, --host HOST
                        Host address to bind. (default: 0.0.0.0)
  -b BASE, --base BASE  Base prefix path for all the URLs. E.g., /v1 (default: None)
```
