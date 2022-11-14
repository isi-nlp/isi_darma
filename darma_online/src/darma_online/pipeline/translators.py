from typing import List

from requests import post
from spacy.lang.en import English
from spacy.lang.fr import French

class Translator:

    def __init__(self, logger):
        self.RTG_API = 'http://spolin.isi.edu:6060/translate'
        self.logger = logger
        # self.eng_sentencizer = English().
        # self.eng_sentencizer.add_pipe('sentencizer')
        self.french_sentencizer = French()
        self.french_sentencizer.add_pipe('sentencizer')
        self.logger.info('French Sentencizers initialized.')

    def split_comment(self, comment:str) -> List[str]:
        doc = self.french_sentencizer(comment)
        split_sentences = [sent.text.strip() for sent in doc.sents]
        # Only return sentences with less than 80 tokens
        split_sentences = [sent for sent in split_sentences if len(sent.split()) < 80]
        self.logger.debug(f'Split french text into sentences: {split_sentences}')
        # Return only 10 sentences
        return split_sentences[:10] if len(split_sentences) > 10 else split_sentences

    def rtg(self, comment_str: str) -> str:
        sentences = self.split_comment(comment_str)
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
