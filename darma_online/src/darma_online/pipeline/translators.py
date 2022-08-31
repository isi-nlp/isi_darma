from requests import post

class Translator:

    def __init__(self, logger):
        self.RTG_API = 'http://spolin.isi.edu:6060/translate'
        self.logger = logger

    def rtg(self, comment_str: str) -> str:
        source = {'source': [comment_str]}
        self.logger.debug(f'Sending source to RTG for translation...')

        try:
            response = post(self.RTG_API, json=source)
            if response.ok:
                response = response.json()
                self.logger.info(f'Received Translated dialogue from RTG: {response["translation"]}')

                return response["translation"][0]
            else:
                self.logger.warning(f'Translation failed with {response.status_code} -> {response.reason}!')
                self.logger.warning(f'Response Body from RTG:\n{response.json()}')
                return comment_str

        except Exception as e:
            self.logger.error(f'Error connecting to RTG API: {e}. Returning original comment.')
            return comment_str
