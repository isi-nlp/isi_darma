from googleapiclient import discovery
from abc import ABC, abstractmethod
from isi_darma.logging_setup import logger
import json


API_KEY = 'AIzaSyC30WbnABE2zjzK4Be58ytkatxgOC3yg9I'

class ModerationClassifier(ABC):

    @abstractmethod
    def needs_moderation(self, toxicity):
        pass
class PerspectiveAPIModerator(ModerationClassifier): 

    def __init__(self) -> None:
        
        self.client = discovery.build(
        "commentanalyzer",
        "v1alpha1",
        developerKey=API_KEY,
        discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
        static_discovery=False,
        )

        self.toxicity_threshold = 0.7

    def needs_moderation(self, toxicity) -> bool: 
        return toxicity >= self.toxicity_threshold

    def measure_toxicity(self, comment) -> float:

        analyze_request = {
            'comment': { 'text': comment },
            'requestedAttributes': {'TOXICITY': {}}
        }

        response = self.client.comments().analyze(body=analyze_request).execute()
        try: 
            toxicity_score = float(response["attributeScores"]["TOXICITY"]["summaryScore"]["value"])
        except Exception as e: 
            logger.info(f"Exception occurred: {e}. Setting toxicity to 0.")
            toxicity_score = 0 
    
        return toxicity_score