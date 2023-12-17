from flask import Flask, request
from api import Api
from setup import Setup

app = Flask(__name__)

@app.route('/event/generate-event/<eventKey>', methods=['POST'])
def generateEvent(eventKey):
    return api.generateEvent(eventKey)


@app.route('/event/clear-event', methods=['DELETE'])
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

@app.route('/pits/add-robot', methods=['POST'])
def addRobot():
    return api.addRobot(request.json)

if __name__ == '__main__':
    setup = Setup()
    if setup.checkSetup():
        api = Api()
        app.run(debug=True)
    else:
        print("Setup not done or missing keys")
        setup.setupKeys()
        if setup.setup:
            print("Setup complete")
            api = Api()
            app.run(debug=True)
        else:
            print("Setup failed")
