from typing import List

from requests import post
from spacy.lang.en import English

class Translator:

    def __init__(self, logger):
        self.RTG_API = 'http://spolin.isi.edu:6060/translate'
        self.logger = logger
        self.sentencizer = English().add_pipe('sentencizer')

    def split_sentences(self, text:str) -> List[str]:
        split_text = [x.text for x in self.sentencizer(text).sents]
        self.logger.debug(f'Split text into sentences: {split_text}')
        return split_text[:80] if len(split_text) > 80 else split_text

    def rtg(self, comment_str: str) -> str:
        sentences = self.split_sentences(comment_str)
        source = {'source': sentences}
        self.logger.debug(f'Sending source sentences to RTG for translation: {source}')

        try:
            response = post(self.RTG_API, json=source)
            if response.ok:
                response = response.json()
                self.logger.info(f'Received Translated dialogue from RTG: {response["translation"]}')
                return ' '.join(response['translation'][0])
            else:
                self.logger.warning(f'Translation failed with {response.status_code} -> {response.reason}!')
                self.logger.warning(f'Response Body from RTG:\n{response.json()}')
                return comment_str

        except Exception as e:
            self.logger.error(f'Error connecting to RTG API: {e}. Returning original comment.')
            return comment_str
