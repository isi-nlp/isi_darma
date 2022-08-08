import json

class DatabaseManager:


    def __init__(self, logger, root = "/isi_darma/isi_darma/src/isi_darma/data"):
        self.logger = logger
        self.root_dir = root
        self.optout_db_path = f'{self.root_dir}/optout/optout_db.json'
        self.moderated_hashes_path = f'{self.root_dir}/moderated_hashes/hashes.json'
        self.optout_db = self.read_db(self.optout_db_path)
        self.moderated_db = self.read_db(self.moderated_hashes_path)


    def read_db(self, path):
        self.logger.info(f"Reading database from {path}")
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.decoder.JSONDecodeError as e:
                self.logger.error(f"Error reading database from {path}", exc_info=True)
                self.logger.debug(f"Returning empty database")
                return {}

    def add_optout_user(self, username: str, dialogue_str: str):
        self.optout_db[username] = { "dialogue": dialogue_str }
        with open(self.optout_db_path, "w") as f:
            f.write(json.dumps(self.optout_db))
        self.logger.info(f"User {username} opted out of darma bot moderation.")


    def search_optout_db(self, username: str) -> bool:
        user_in_optout = username in self.optout_db.keys()
        self.logger.info(f"User {username} is {'present' if user_in_optout else 'not present'} in the optout database.")
        return user_in_optout


    def add_to_moderated(self, obj_id: str, author: str, body: str):
        self.moderated_db[obj_id] = {
                                            "author": author,
                                            "content": body
                                        }
        with open(self.moderated_hashes_path, "w") as f:
            f.write(json.dumps(self.moderated_db))
        self.logger.info(f"Id - {obj_id} added to the moderated database.")


    def search_moderated(self, obj_id: str) -> bool:
        """
        Check if the hash is in the list of moderated hashes
        """
        is_moderated = obj_id in self.moderated_db.keys()
        self.logger.info(f"Hash {obj_id} is {'present' if is_moderated else 'not present'} in the moderated database")

        return is_moderated

