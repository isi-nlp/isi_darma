from googleapiclient import discovery
from abc import ABC, abstractmethod

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

		self.toxicity_threshold = 0.7
		self.logger = logger

	def needs_moderation(self, toxicity) -> bool:
		return toxicity >= self.toxicity_threshold

	def measure_toxicity(self, comment) -> float:

		analyze_request = {
			'comment': {'text': comment},
			'requestedAttributes': {'TOXICITY': {}}
		}

		response = self.client.comments().analyze(body=analyze_request).execute()
		try:
			toxicity_score = float(response["attributeScores"]["TOXICITY"]["summaryScore"]["value"])
		except Exception as e:
			self.logger.info(f"Exception occurred: {e}. Setting toxicity to 0.")
			toxicity_score = 0

	def map_behavtypes(self, toxicity_scores):
		mapping = {
					"namecalling": toxicity_scores["attributeScores"]["INSULT"]["summaryScore"]["value"],
					"ad-hominem attack": toxicity_scores["attributeScores"]["IDENTITY_ATTACK"]["summaryScore"]["value"],
					"obscenities/vulgarities": toxicity_scores["attributeScores"]["PROFANITY"]["summaryScore"]["value"],
					"dehumanization": toxicity_scores["attributeScores"]["THREAT"]["summaryScore"]["value"]
				}

		self.logger.debug(f"Toxicity scores after mapping: {mapping}")
		behav_type = max(mapping.items(), key=operator.itemgetter(1))[0]
		self.logger.info(f"Current max Toxicity Behaviour type: {behav_type} with score {mapping[behav_type]}")
		return mapping[behav_type], behav_type

	def get_behavTypes(self, behavtype_endpoint, endpoint):
		endpoint_health = get(endpoint).status_code
		if endpoint_health == 200:
			behav_types = get(behavtype_endpoint).json()
			self.logger.info(f"Current tracking Toxicity Behaviour types: {behav_types}")
			return behav_types
		else:
			self.logger.info(f"Endpoint {endpoint} is not healthy. Returning status code {endpoint_health}.")
			return {}
