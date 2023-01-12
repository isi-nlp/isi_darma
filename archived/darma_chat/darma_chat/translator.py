from abc import ABC, abstractmethod
import logging as log
from typing import List

import requests
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from spacy.lang.en import English


nlp = English()
nlp.add_pipe('sentencizer')


def split_sentences(text:str) -> List[str]:
    return [x.text for x in nlp(text).sents]


class BaseTranslator(ABC):

    @abstractmethod
    def translate(self, text: str, src_lang: str, tgt_lang: str, **args) -> str:
        pass

    def __call__(self, text, *args, **kwds) -> str:
        return self.translate(text, *args, **kwds)


class RtgApiTranslator(BaseTranslator):

    def __init__(self, api_url: str) -> None:
        self.api_url = api_url

    def _translate(self, req_data, out_key='translation'):
        log.debug(f'Sending to {self.api_url} :: {req_data}')
        response = requests.post(self.api_url, json=req_data)
        if response.ok:
            resp_data = response.json()
            log.info(f'RTG translation: {resp_data[out_key]}')
            return resp_data[out_key]
        else:
            log.warning(f'Response Body:\n{response.json()}')
            raise Exception(
                f'Translation failed {response.status_code} -> {response.reason}')

    def translate(self, text: str, src_lang='mul', tgt_lang='eng') -> str:
        req_data = {'source': split_sentences(text)}
        try:
            return ' '.join(self._translate(req_data=req_data))
        except Exception as e:
            log.error(f'MT API Error:: {e}. Returning source.')
            return text


class NLLBApiTranslator(RtgApiTranslator):

    def __init__(self, api_url: str, src_lang: str, tgt_lang: str) -> None:
        super().__init__(api_url)
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

    def translate(self, text: str, src_lang=None, tgt_lang=None) -> str:
        req_data = dict(source=split_sentences(text),
                        src_lang=src_lang or self.src_lang,
                        tgt_lang=tgt_lang or self.tgt_lang)
        try:
            return ' '.join(self._translate(req_data=req_data))
        except Exception as e:
            log.error(f'MT API Error:: {e}. Returning source.')
            return text


class HuggingFaceTranslator(BaseTranslator):

    def __init__(self, model='Helsinki-NLP/opus-mt-en-fr') -> None:
        self.model_id = model
        self.model = AutoTokenizer.from_pretrained(self.model_id)
        self.tokenizer = AutoModelForSeq2SeqLM.from_pretrained(self.model_id)

    def translate(self, text: str, src_lang='mul', tgt_lang='eng') -> str:
        log.debug(f"Translating {text}...")
        batch = self.tokenizer([text], return_tensors="pt")
        gen = self.model.generate(**batch)
        fr_response = self.tokenizer.batch_decode(
            gen, skip_special_tokens=True)
        return fr_response[0]


# TODO add other MTs
registry = {
    'rtg_api': RtgApiTranslator,
    'huggingface': HuggingFaceTranslator,
    'nllb_api': NLLBApiTranslator,
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
