import os
import dotenv

class Setup:
    def __init__(self):
        dotenv.load_dotenv()
        self.keys = {
            'tbaApiKey': bool(os.getenv('TBA_KEY')),
            'mongoURI': bool(os.getenv('MONGO_URI')),
            'mongoUser': bool(os.getenv('MONGO_USER')),
            'mongoPassword': bool(os.getenv('MONGO_PASSWORD')),
            'apiPassword': bool(os.getenv('API_PASSWORD'))
        }
        self.missingKeys = []
        try:
            self.setup = bool(os.getenv('SETUP'))
        except KeyError:
            raise KeyError("Setup error")


    def setupKeys(self):
        print("Missing keys: ")
        for key in self.keys:
            if not self.keys[key]:
                print("\t -"+key)
                self.missingKeys.append(key)
        print(self.missingKeys)
        if 'tbaApiKey' in self.missingKeys:
            self.setTBAKey()
        if 'apiPassword' in self.missingKeys:
            self.setApiPassword()
        if 'mongoUser' in self.missingKeys:
            self.setMongoUser()
        if 'mongoPassword' in self.missingKeys:
            self.setMongoPassword()
        if 'mongoURI' in self.missingKeys:
            if not self.keys['mongoUser'] or not self.keys['mongoPassword']:
                print("You need to set the user and password before setting the URI")
                return
            self.setMongoURI()

        for key in self.keys:
            if not self.keys[key]:
                self.setup = False
                return
        self.setup = True
        dotenv.set_key('.env', 'SETUP', 'True')

    def setTBAKey(self):
        key = ""
        while key == "":
            key= input("Enter your TBA API key: ")
            if key == "":
                print("Key cannot be empty")
        dotenv.set_key('.env', 'TBA_KEY', key)
        self.keys['tbaApiKey'] = True
        print("Key set")


    def setMongoUser(self):
        user = ""
        while user == "":
            user = input("Enter your MongoDB username: ")
            if user == "":
                print("User cannot be empty")
        dotenv.set_key('.env', 'MONGO_USER', user)
        self.keys['mongoUser'] = True
        print("Key set")


    def setMongoPassword(self):
        password = ""
        while password == "":
            password = input("Enter your MongoDB password: ")
            if password == "":
                print("Password cannot be empty")
        dotenv.set_key('.env', 'MONGO_PASSWORD', password)
        self.keys['mongoPassword'] = True
        print("Key set")


    def setMongoURI(self):
        uri = ""
        while uri == "":
            uri = input("Enter your MongoDB URI: ")
            if uri == "":
                print("URI cannot be empty")
        dotenv.set_key('.env', 'MONGO_URI', uri)
        self.keys['mongoURI'] = True
        print("Key set")


    def setApiPassword(self):
        password = ""
        while password == "":
            password = input("Enter your API password: ")
            if password == "":
                print("Password cannot be empty")
        dotenv.set_key('.env', 'API_PASSWORD', password)
        self.keys['apiPassword'] = True
        print("Key set")

    def checkSetup(self):
        return self.setup