from abc import ABC, abstractmethod
from logging import Logger

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
	def get_random_comtype_resp(usernames=['others']):
		usernames = ",".join(usernames)
		comtype_responses = [
			f"Veuillez cesser de faire cela et vous comporter correctement!",
			f"Vous avez eu un comportement de ce genre en répondant à {usernames}",
			f"Je me sens contrarié parce que même si je ne connais pas {usernames}, le langage que vous avez utilisé pour communiquer avec eux me bouleverserait.",
			f"Est-ce parce que vous êtes en colère contre {usernames} parce qu'ils ont des croyances différentes des vôtres?",
			f"Voulez-vous que {usernames} changent d'opinion et peut-être convaincre d'autres personnes qui partagent actuellement leurs opinions de changer également?"
		]
		return random.sample(comtype_responses, 1)[0]
