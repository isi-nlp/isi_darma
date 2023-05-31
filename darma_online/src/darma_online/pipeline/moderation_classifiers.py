from googleapiclient import discovery
from abc import ABC, abstractmethod
from requests import get, post
import operator
import time
import pandas as pd
import os

API_KEY = 'AIzaSyC30WbnABE2zjzK4Be58ytkatxgOC3yg9I'

class ModerationClassifier(ABC):

    @abstractmethod
    def needs_moderation(self, toxicity):
        pass


class PerspectiveAPIModerator(ModerationClassifier):

    def __init__(self, logger, config) -> None:

        self.perspec_client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=API_KEY,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
            static_discovery=False,
        )

        self.logger = logger

        self.toxicity_threshold = config["toxicity_threshold"]
        self.use_moderator = config["use_moderator"]
        self.moderator_endpoint = "http://128.9.37.116:5050/moderation-prediction-classifier"
        if not self.use_moderator:
            self.logger.info("Not using moderator. Moderator score will be set to 1 for all comments!")

        self.csv_path = config["intersection_scores_path"]
        COLUMNS = ['comment', 'moderator_score', 'perspec_tox_score', 'det_behav_type', 'namecalling' ,'ad_hominem_attacking', 'obscene_vulgar','dehumanizing']
        self.intersect_csv = "intersection_scores"
        self.mod_agree_csv = "mod_agree"

        # Data collection for intersection scores - disagreement
        if os.path.exists(f"{self.csv_path}/{self.intersect_csv}.csv"):
            self.intersection_df = pd.read_csv(f"{self.csv_path}/{self.intersect_csv}.csv", header=0)
        else:
            self.intersection_df = pd.DataFrame(columns=COLUMNS)

        # Data collection for agreed moderation
        if os.path.exists(f"{self.csv_path}/{self.mod_agree_csv}"):
            self.mod_agree_df = pd.read_csv(f"{self.csv_path}/{self.mod_agree_csv}.csv", header=0)
        else:
            self.mod_agree_df = pd.DataFrame(columns=COLUMNS)

    def needs_moderation(self, toxicity) -> bool:
        return toxicity >= self.toxicity_threshold

    def measure_toxicity(self, comment, hashid=None) -> (float, str):

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
            perspec_response = self.perspec_client.comments().analyze(body=analyze_request).execute()
            perspec_decision, perspec_score_mapping, perspec_tox_score, perspec_behav_score, behav_type = self.map_behavtypes(perspec_response)

            if self.use_moderator:
                moderator_score = self.get_moderator_response(comment)
            else:
                moderator_score = 1

            final_decision = self.intersect_moderation(comment, moderator_score, perspec_tox_score, perspec_score_mapping['behav_types'], behav_type)
            return final_decision, perspec_tox_score, perspec_behav_score, behav_type

        except Exception as e:
            if e.status_code == 429:
                self.logger.debug(f"API rate limit reached. Waiting for 60 seconds.")
                time.sleep(60)
                self.logger.debug(f'Retrying toxicity measurement for comment: {analyze_request["comment"]["text"]}')
                final_decision, perspec_score, behav_type = self.measure_toxicity(comment)
            else:
                self.logger.error(f"Exception occurred with code: {e} for comment. Setting toxicity to 0 with empty behaviour type.")
                final_decision, perspec_score, behav_type = False, 0, ""

        return final_decision, perspec_score, behav_type

    def map_behavtypes(self, toxicity_scores):
        mapping = {
                    "toxicity": toxicity_scores["attributeScores"]["TOXICITY"]["summaryScore"]["value"],
                    "severe_toxicity": toxicity_scores["attributeScores"]["SEVERE_TOXICITY"]["summaryScore"]["value"],
                    "behav_types": {
                        "namecalling": toxicity_scores["attributeScores"]["INSULT"]["summaryScore"]["value"],
                        "ad-hominem_attacking": toxicity_scores["attributeScores"]["IDENTITY_ATTACK"]["summaryScore"]["value"],
                        "obscene/vulgar": toxicity_scores["attributeScores"]["PROFANITY"]["summaryScore"]["value"],
                        "dehumanizing": toxicity_scores["attributeScores"]["THREAT"]["summaryScore"]["value"]
                    }
                }

        self.logger.info(f"Perspective Toxicity scores after mapping: {mapping}")
        behav_type = max(mapping["behav_types"].items(), key=operator.itemgetter(1))[0]
        tox_score = max(mapping['toxicity'], mapping['severe_toxicity'])
        behav_score = mapping["behav_types"][behav_type]

        self.logger.info(f"Current max Toxicity Behaviour type is '{behav_type}' with behav score = {behav_score} and toxicity score = {tox_score}")

        if self.needs_moderation(mapping["toxicity"]) or self.needs_moderation(mapping["severe_toxicity"]):
            needs_mod = True
        else:
            self.logger.info(f'Perspective Toxicity score: {mapping["toxicity"]} or Severe Toxicity score: {mapping["severe_toxicity"]} is below threshold {self.toxicity_threshold}.')
            needs_mod = False

        return needs_mod, mapping, tox_score, behav_score, behav_type

    def get_moderator_response(self, comment):
        request_data = { "0": { "comment" : comment } }
        try:
            resp = post(self.moderator_endpoint, json=request_data)
            if resp.status_code == 200:
                self.logger.info(f'Moderator score = {resp.json()["0"]["score"]}')
                return resp.json()["0"]["score"]
            else:
                self.logger.warning(f"{resp.status_code} status code from Moderator: {resp}")
                return resp.status_code
        except Exception as e:
            self.logger.error(f"Exception occurred while getting moderator response: {e}")
            return 0

    def intersect_moderation(self, comment, moderator_score, perspec_tox_score, behav_scores, behav_type):
        data_row = [comment, moderator_score, perspec_tox_score, behav_type, behav_scores["namecalling"], behav_scores["ad-hominem_attacking"], behav_scores["obscene/vulgar"], behav_scores["dehumanizing"]]

        if self.needs_moderation(perspec_tox_score) and self.needs_moderation(moderator_score):
            self.logger.info("Moderator and Perspective API both agree that comment needs moderation.")
            # TODO: Also save hashid of comment
            self.mod_agree_df = self.dump_data(self.mod_agree_df, data_row, self.mod_agree_csv)
            return True
        else:
            self.intersection_df = self.dump_data(self.intersection_df, data_row, self.intersect_csv)
            self.logger.info(f"Moderator = {moderator_score} and Perspective = {perspec_tox_score}, DISAGREE about moderation. Data saved to {self.csv_path}/intersection_scores.csv")
            return False

    def dump_data(self, dataframe, data_row, csv_name):
        # Insert the new row data in the dataframe
        dataframe.loc[len(dataframe)] = data_row

        # Dump intersection scores to csv and reload
        dataframe.to_csv(f"{self.csv_path}/{csv_name}.csv", index=False)
        dataframe = pd.read_csv(f"{self.csv_path}/{csv_name}.csv", header=0)
        self.logger.debug(f"Saved data to {self.csv_path}/{csv_name}.csv")

        return dataframe
