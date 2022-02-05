from abc import ABC, abstractmethod
import requests
from loguru import logger
from typing import List

SPOLIN_ENDPOINT = "https://spolin.isi.edu/ya_back/api"


class ResponseGenerator(ABC):

    @abstractmethod
    def generate_response(self):
        pass


class SpolinBotRG(ResponseGenerator):

    def __init__(self, endpoint: str = SPOLIN_ENDPOINT):
        self.api_endpoint = endpoint

    def generate_response(self, incoming_dialogue: List[str]):
        if isinstance(incoming_dialogue, str): 
            incoming_dialogue = [incoming_dialogue]
            
        data = {
            "new_message": incoming_dialogue,
            "message_list": [], # previous dialogue that has already been tokenized. only needed for live chat and time critical cases
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
