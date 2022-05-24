from requests import post
from transformers import MarianTokenizer, MarianMTModel


class Translator:

    def __init__(self, logger, french=True):
        self.RTG_API = 'http://localhost:6060/translate'
        self.logger = logger

        if french:
            self.fr_model_name = f"Helsinki-NLP/opus-mt-en-fr"
            self.fr_mt_model = MarianMTModel.from_pretrained(self.fr_model_name)
            self.fr_tokenizer = MarianTokenizer.from_pretrained(self.fr_model_name)
            self.logger.info(f"{self.fr_model_name} model loaded for Eng to French Translation")

    def rtg(self, comment_str: str) -> str:
        source = {'source': [comment_str]}
        self.logger.debug(f'Sending source to RTG for translation: {source}')

        try:
            response = post(self.RTG_API, json=source)
            if response.ok:
                response = response.json()
                self.logger.info(f'Received translation from RTG for {response["source"]} -> {response["translation"]}')
                return response["translation"][0]
            else:
                self.logger.warning(f'Translation failed with {response.status_code} -> {response.reason}!')
                self.logger.warning(f'Response Body from RTG:\n{response.json()}')
                return comment_str

        except Exception as e:
            self.logger.error(f'Error connecting to RTG API: {e}')
            return comment_str

    def fran_translator(self, eng_response: str) -> str:
        self.logger.debug(f"Translating best english response to french...")
        batch = self.fr_tokenizer([eng_response], return_tensors="pt")
        gen = self.fr_mt_model.generate(**batch)
        fr_response = self.fr_tokenizer.batch_decode(gen, skip_special_tokens=True)
        return fr_response[0]
