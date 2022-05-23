from googleapiclient import discovery
from abc import ABC, abstractmethod
from requests import get, post
import operator

API_KEY = 'AIzaSyC30WbnABE2zjzK4Be58ytkatxgOC3yg9I'


class ModerationClassifier(ABC):

	@abstractmethod
	def needs_moderation(self, toxicity):
		pass


class PerspectiveAPIModerator(ModerationClassifier):

	def __init__(self, logger) -> None:

		self.client = discovery.build(
			"commentanalyzer",
			"v1alpha1",
			developerKey=API_KEY,
			discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
			static_discovery=False,
		)

		self.toxicity_threshold = 0.5
		self.logger = logger
		self.toxicity_endpoint = "http://effectmed01.isi.edu:5001/"
		self.tox_classifier_behavtypes = "http://effectmed01.isi.edu:5001/v1/toxicity/types"
		self.tox_classifier_endpoint = "http://effectmed01.isi.edu:5001/v1/toxicity/"

	# self.behav_types = self.get_behavTypes(self.tox_classifier_behavtypes, self.toxicity_endpoint)

	def needs_moderation(self, toxicity) -> bool:
		return toxicity >= self.toxicity_threshold

	def measure_toxicity(self, comment) -> (float, str):

		analyze_request = {
			'comment': {'text': comment},
			'requestedAttributes': {
				'TOXICITY': {},
				'SEVERE_TOXICITY': {},
				'IDENTITY_ATTACK': {},
				'INSULT': {},
				'PROFANITY': {},
				'THREAT': {},
			}
		}

		try:
			response = self.client.comments().analyze(body=analyze_request).execute()
			toxicity_score, behav_type = self.map_behavtypes(response)

		except Exception as e:
			self.logger.debug(f"Exception occurred: {e} for comment: {analyze_request['comment']['text']}. Setting toxicity to 0 with empty behaviour type.")
			toxicity_score, behav_type = 0, ""

		return toxicity_score, behav_type

	def map_behavtypes(self, toxicity_scores):
		mapping = {
					"toxicity": toxicity_scores["attributeScores"]["TOXICITY"]["summaryScore"]["value"],
					"severe toxicity": toxicity_scores["attributeScores"]["SEVERE_TOXICITY"]["summaryScore"]["value"],
					"behav_types": {
						"namecalling": toxicity_scores["attributeScores"]["INSULT"]["summaryScore"]["value"],
						"ad-hominem attacking": toxicity_scores["attributeScores"]["IDENTITY_ATTACK"]["summaryScore"]["value"],
						"obscene/vulgar": toxicity_scores["attributeScores"]["PROFANITY"]["summaryScore"]["value"],
						"dehumanizing": toxicity_scores["attributeScores"]["THREAT"]["summaryScore"]["value"]
					}
				}

		self.logger.debug(f"Toxicity scores after mapping: {mapping}")

		if self.needs_moderation(mapping["toxicity"]) or self.needs_moderation(mapping["severe toxicity"]):
			behav_type = max(mapping["behav_types"].items(), key=operator.itemgetter(1))[0]
			score = mapping[behav_type]
			self.logger.info(f"Current max Toxicity Behaviour type: {behav_type} with score {mapping[behav_type]}")

		else:
			self.logger.info(f'Toxicity score: {mapping["toxicity"]} or Severe Toxicity score: {mapping["severe toxicity"]} is below threshold {self.toxicity_threshold}. Setting behaviour type to empty string.')
			score, behav_type = 0.0, ""

		return score, behav_type

	def get_behavTypes(self, behavtype_endpoint, endpoint):
		endpoint_health = get(endpoint).status_code
		if endpoint_health == 200:
			behav_types = get(behavtype_endpoint).json()
			self.logger.info(f"Current tracking Toxicity Behaviour types: {behav_types}")
			return behav_types
		else:
			self.logger.info(f"Endpoint {endpoint} is not healthy. Returning status code {endpoint_health}.")
			return {}
