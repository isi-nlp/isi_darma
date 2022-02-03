from abc import ABC, abstractmethod
import requests
from src.logging_setup import logger

SPOLIN_ENDPOINT = "https://spolin.isi.edu/ya_back/api"


class ResponseGenerator(ABC):

    @abstractmethod
    def generate_response(self):
        pass


class SpolinBotRG(ResponseGenerator):

    def __init__(self, endpoint: str = SPOLIN_ENDPOINT):
        self.api_endpoint = endpoint

    def generate_response(self, incoming_message):
        data = {
            "new_message": [incoming_message],
            "message_list": [],
            "forward_temp": "1.0",
            "mmi_temp": "0.7",
            "top_k": "20",
        }

        r = requests.post(url=SPOLIN_ENDPOINT, json=data)
        response_json = r.json()
        # returned format: {'responses: [[response1, score1], [response2, score2]...]}

        best_response = response_json["responses"][0][0]
        logger.info(f"Generated response: {best_response}")

        return best_response
