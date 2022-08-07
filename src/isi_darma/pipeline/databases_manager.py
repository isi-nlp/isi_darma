import json

class DatabaseManager:

    def __init__(self, logger, root = "isi_darma/data"):
        self.logger = logger
        self.root_dir = root
        self.optout_db_path = f'{self.root_dir}/optout/optout_db.json'
        self.moderated_hashes_path = f'{self.root_dir}/moderated_hashes/hashes.json'
        self.optout_db = self.read_db(self.optout_db_path)
        self.moderated_db = self.read_db(self.moderated_hashes_path)

    @staticmethod
    def read_db(path):
        with open(path, 'r') as f:
            return json.load(f)

    def add_optout_user(self, username: str, dialogue_str: str):
        self.optout_db[username] = { "dialogue": dialogue_str }
        with open(self.optout_db_path, "w") as f:
            f.write(json.dumps(self.optout_db))
        self.logger.info(f"User {username} opted out of darma bot moderation.")

    def search_optout_db(self, username: str) -> bool:
        user_in_optout = username in self.optout_db.keys()
        self.logger(f"User {username} is {'present' if user_in_optout else 'not present'} in the optout database.")
        return user_in_optout