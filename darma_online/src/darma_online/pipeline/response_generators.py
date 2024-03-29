from abc import ABC, abstractmethod
from logging import Logger

import json
import random
import requests
from typing import List

SPOLIN_ENDPOINT = "https://spolin.isi.edu/ya_back/api"


class ResponseGenerator(ABC):

    @abstractmethod
    def generate_response(self):
        pass


class SpolinBotRG(ResponseGenerator):

    def __init__(self, logger: Logger, endpoint: str = SPOLIN_ENDPOINT):
        self.logger = logger
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
        self.logger.info(f"Generated response: {best_response}")

        return best_response

    @staticmethod
    def get_random_resp(responses: List[str], usernames: List[str] = None):

        if usernames is None:
            usernames = responses['others']

        usernames = ",".join(usernames)

        selected_response = random.sample(responses['nvc_responses'], 1)[0]
        selected_response = selected_response.replace("<usernames>", usernames)

        return selected_response

    @staticmethod
    def read_responses(path : str = "/darma_online/darma_online/src/darma_online/data/response_templates/responses.json"):
        """
        Read the json file for bot info.
        """
        return json.loads(open(path, "r").read())