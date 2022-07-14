from abc import ABC, abstractmethod
import requests
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

import logging as log


class BaseTranslator(ABC):

    @abstractmethod
    def translate(self, text: str, src_lang: str, tgt_lang: str, **args) -> str:
        pass

    def __call__(self, text, *args, **kwds) -> str:
        return self.translate(text, *args, **kwds)


class RtgApiTranslator(BaseTranslator):

    def __init__(self, api_url='http://rtg.isi.edu/many-eng/v1/translate') -> None:
        self.api_url = api_url

    def translate(self, text: str, src_lang ='mul', tgt_lang='eng') -> str:
        source = {'source': [text]}
        log.debug(f'Sending source to RTG for translation: {source}')
        try:
            response = requests.post(self.api_url, json=source)
            if response.ok:
                response = response.json()
                log.info(f'RTG translation: {response["translation"]}')
                return response["translation"][0]
            else:
                log.warning(f'Translation failed {response.status_code} -> {response.reason}')
                log.warning(f'Response Body from RTG:\n{response.json()}')
                return text
        except Exception as e:
            log.error(f'Error connecting to RTG API: {e}. Returning source.')
            return text


class HuggingFaceTranslator(BaseTranslator):

    def __init__(self, model='Helsinki-NLP/opus-mt-en-fr') -> None:
        self.model_id = model
        self.model = AutoTokenizer.from_pretrained(self.model_id)
        self.tokenizer = AutoModelForSeq2SeqLM.from_pretrained(self.model_id)

    def translate(self, text: str, src_lang ='mul', tgt_lang='eng') -> str:
        log.debug(f"Translating {text}...")
        batch = self.tokenizer([text], return_tensors="pt")
        gen = self.model.generate(**batch)
        fr_response = self.tokenizer.batch_decode(gen, skip_special_tokens=True)
        return fr_response[0]



# TODO add other MTs
registry = {
    'rtg_api': RtgApiTranslator,
    'huggingface': HuggingFaceTranslator
}


def get_translator(name, args):
    assert name in registry, f'{name} is invalid; supported: {registry.keys}'
    log.info(f"creating MT: name={name} args={args}")
    args = args or dict()
    return registry[name](**args)


class DialogTranslator:

    def __init__(self, pre_translator, post_translator=None) -> None:
        assert pre_translator or post_translator,\
            'Both pre- and post- processing MTs are None. Expected atleast one.'
        log.info(f"Preprocess MT: {pre_translator}")
        log.info(f"Postprocess MT: {post_translator}")
        self.pre_translator = pre_translator
        self.post_translator = post_translator

    def maybe_preprocess(self, text):
        if not self.pre_translator:
            return text
        return self.pre_translator(text)

    def maybe_postprocess(self, text):
        if not self.post_translator:
            return text
        return self.post_translator(text)
