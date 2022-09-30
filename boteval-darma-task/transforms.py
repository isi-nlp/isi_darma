import requests

from boteval import registry as R, log
from boteval.transforms import BaseTransform, SpacySplitter
from boteval.model import ChatMessage


@R.register(R.TRANSFORM, name='rtg-api')
class RtgApiTranslator(BaseTransform):

    def __init__(self, api_url: str) -> None:
        super().__init__()
        self.api_url = api_url
        self.splitter = SpacySplitter.get_instance()

    def translate(self, req_data, out_key='translation'):
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

    def transform(self, msg: ChatMessage) -> ChatMessage:
        try:
            text_orig = msg.text
            req_data = {'source': self.splitter(text_orig)}
            msg.text = ' '.join(self.translate(req_data=req_data))
            msg.data['text_orig'] = text_orig
        except Exception as e:
            log.error(f'MT API Error:: {e}.')
        return msg

@R.register(R.TRANSFORM, name='nllb-api')
class NLLBApiTranslator(RtgApiTranslator):

    def __init__(self, api_url: str, src_lang: str, tgt_lang: str) -> None:
        super().__init__(api_url)
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

    def transform(self, msg: ChatMessage) -> ChatMessage:
        try:
            text_orig = msg.text
            req_data = dict(
                source=self.splitter(text_orig),
                src_lang=self.src_lang,
                tgt_lang=self.tgt_lang)
            msg.text = ' '.join(self.translate(req_data=req_data))
            msg.data['text_orig'] = text_orig
        except Exception as e:
            log.error(f'MT API Error:: {e}.')
        return msg
