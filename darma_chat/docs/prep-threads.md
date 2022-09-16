
# Prepare Threads

We have `python -m darma_chat.prep_threads` tool that can help prepare threads.
Preparation involves three optional transformations:
* Unmarkdown:  `--unmarkdown | --no-unmarkdown`
* Anonymization: `--anonymize | --no-anonymize`
* Machine Translation: `--mt | --no-mt` 


```bash
$  python -m darma_chat.prep_threads -h
usage: prep_threads.py [-h] -i INP -o OUT [--anonymize | --no-anonymize] [--unmarkdown | --no-unmarkdown] [--mt | --no-mt] [-mt-api MT_API]

optional arguments:
  -h, --help            show this help message and exit
  -i INP, --inp INP     Input file path (default: None)
  -o OUT, --out OUT     Output path (default: None)
  --anonymize           Anonymize thread (default: False)
  --no-anonymize        Anonymize thread (default: True)
  --unmarkdown          Remove markdown tags from text (default: True)
  --no-unmarkdown       Remove markdown tags from text (default: False)
  --mt                  Machine translate text (default: True)
  --no-mt               Machine translate text (default: False)
  -mt-api MT_API, --mt-api MT_API
                        MT API URL (default: http://54.68.184.232:6060/many-eng/v1/translate)
```

# Example:

 ```bash
 python -m darma_chat.prep_threads --no-anonymize --unmarkdown \
   --mt --mt-api http://rtg.isi.edu/many-eng/v1/translate \
   -i input_threads.json -o prepared_threads.json
 ```

