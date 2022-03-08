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
			f'Please quit doing that and behave!',
			f'You used this kind of behavior in response to {usernames}.',
			f'You used this kind of behavior in response to {usernames}. I feel upset because even though I don’t know {usernames}, the language you used when communicating with them would make me upset.',
			f'You used this kind of behavior in response to {usernames}. Is this because you are angry at {usernames} for having beliefs that are different from yours?',
			f'You used this kind of behavior in response to {usernames}. Is this because you are angry at {usernames} for having beliefs that are  different from yours? Do you want {usernames} to change their opinions and perhaps convince others who currently share their opinions to also change?'
		]
		return random.sample(comtype_responses, 1)[0]
