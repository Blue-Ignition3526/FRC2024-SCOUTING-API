from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os


class MongoConnection:
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv('MONGO_URI')
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        self.db = self.client['Scouting']

    def test(self):
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(e)
            return False
