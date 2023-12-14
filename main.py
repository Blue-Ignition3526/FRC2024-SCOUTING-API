from dotenv import load_dotenv
from flask import Flask, request
from api import Api
import os

load_dotenv()
tbaKey = os.getenv('TBA_KEY')

app = Flask(__name__)

api = Api()


@app.route('/event/generate-event/<eventKey>', methods=['POST'])
def generateEvent(eventKey):
    return api.generateEvent(eventKey)


@app.route('/event/clear-event', methods=['POST'])
def clearEvent():
    return api.clearEvent()


@app.route('/event/active-event', methods=['GET'])
def activeEvent():
    return api.getActiveEvent()


@app.route('/server/status', methods=['GET'])
def status():
    return api.status()


@app.route('/server/enable', methods=['POST'])
def enable():
    return api.enable()


@app.route('/server/disable', methods=['POST'])
def disable():
    return api.disable()


@app.route('/mongo/status', methods=['GET'])
def checkMongo():
    return api.checkMongo()


@app.route('/matches/add-match', methods=['POST'])
def addMatch():
    return api.addMatch(request.json)

@app.route('/matches/add-multiple-matches', methods=['POST'])
def addMultipleMatches():
    return api.addMultipleMatches(request.json)

if __name__ == '__main__':
    app.run(debug=True)
