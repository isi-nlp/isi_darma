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
python -m chat_admin path-to-config.yml -d
```

# Deployment
```bash
python -m chat_admin path-to-config.yml
```

This starts a service on http://localhost:6060 by default.


## Config file

Here is an example
```yaml
chat_dir: ../darma_chat/darma_chat/model_chat
mturk_profile: default    # the [default] profile in ~/.aws/credentials file
```

* `chat_dir` -- path to directory having JSON files stored by `darma_chat`.
* If `mturk_profile` value is the name of credential profile in `~/.aws/credentials` to be used for authentication with AWS/mturk APIs.



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
```

## Security Notes:
* Authentication is not yet built into admin web UI.
* Currently, the web server  binds to loopback interface `127.0.0.1`. This is intentional, as only the requests coming from same node are accepted.
* If this web UI is deployed on a remote server, use ssh tunnel (e.g. `ssh -L 6060:localhost:6060 <server>`) to establish connection with server. This way, ssh takes care of authentication and only people with ssh access to the remote server can access the admin UI.
