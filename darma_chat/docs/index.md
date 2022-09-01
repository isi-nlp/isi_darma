
# Darma Chat Docs

* Most of the setup docs are in [README](../README.md)
* For MT backend setup, go to [setup-mt-backend.md](./setup-mt-backend.md)
* For preparing initial seed conversations/threads, go to [prep-threads.md](./prep-threads.md)



# Mephisto Set Locales

Edit `~/.mephisto.config.yml` and include this in the top level

```yaml
mturk:
  # French countries https://www.worlddata.info/languages/french.php
  allowed_locales:
    - Country: US
    - Country: CA
    - Country: FR
    - Country: GB
    - Country: AU
    - Country: BE
    - Country: HT
    - Country: CH
    - Country: CD
```
