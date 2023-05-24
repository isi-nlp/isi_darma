# Bot eval DARMA Task


## Links: 

* Bot eval docs are at http://cutelab.name/boteval/ 
* Setting up MT Backend Services:  [darma_chat/docs/setup-mt-backend.md](https://github.com/isi-nlp/isi_darma/blob/main/darma_chat/docs/setup-mt-backend.md)
* Preparing initial seed threads [darma_chat/docs/prep-threads.md](https://github.com/isi-nlp/isi_darma/blob/main/darma_chat/docs/prep-threads.md)
  >  this is probably outdated; check `chat_topics.json` for format. Hint: we need to include `id` and `name` for each topic




## Deployment

Nginx setup with https/SSL  http://cutelab.name/boteval/#nginx
The actual nginx config to be used for darma task on darmaeval.cutelab.name is in the same dir as this README with file name `darmaeval.nginx.conf`


The `darmaeval.nginx.conf` has following URL mappings:

| External URL | Internal URL |
|----------    |--------------|
| `/boteval`   |  http://127.0.0.1:7070/boteval |
| `/boteval-dev1`   |  http://127.0.0.1:7071/boteval-dev1 |
| `/boteval-dev2`   |  http://127.0.0.1:7072/boteval-dev2 |
| `/boteval-stage`   |  http://127.0.0.1:7073/boteval-stage |
| `/boteval-prod`   |  http://127.0.0.1:7074/boteval-prod |

By respecting these mappings help avoid any potential conflicts/collisions. This way, we can use same remote node with single SSL/nginx for development and production. 
For all these URL mappings, the `flask_config.SERVER_NAME` is same which is `darmaeval.cutelab.name`. We need to explicitely inform the app about its url prefix `/boteval` via CLI, as described in the following sections. 

### Development:

We have three settings for developments i.e., three developers can simultaneously run instances on same node.

```bash
# One of these
python  -m boteval darma-task  -d -p 7070 -b /boteval
python  -m boteval darma-task  -d -p 7071 -b /boteval-dev1
python  -m boteval darma-task  -d -p 7072 -b /boteval-dev2

# Or you may also use uwsgi
uwsgi --http 127.0.0.1:7072 --module boteval.app:app --pyargv "darma-task -d -b /boteval-dev2"
```

### Staging

```bash
python  -m boteval darma-task -p 7073 -b /boteval-stage
# or with uwsgi (recommended)
uwsgi --http 127.0.0.1:7073 --module boteval.app:app\
   --pyargv "darma-task -b /boteval-stage"
```

### Production

```bash
python  -m boteval darma-task -p 7074 -b /boteval-prod
# or with uwsgi (recommended)
uwsgi --http 127.0.0.1:7074 --module boteval.app:app \
    --pyargv "darma-task -b /boteval-prod"
```


