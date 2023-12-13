from dotenv import load_dotenv
from flask import Flask
from api import Api
import os

load_dotenv()
tbaKey = os.getenv('TBA_KEY')

app = Flask(__name__)

api = Api()


@app.route('/event/generate-event/<eventKey>')
def generateEvent(eventKey):
    return api.generateEvent(eventKey)


@app.route('/event/clear-event')
def clearEvent():
    return api.clearEvent()


@app.route('/event/active-event')
def activeEvent():
    return api.getActiveEvent()


@app.route('/server/status')
def status():
    return api.status()


@app.route('/server/enable')
def enable():
    return api.enable()


@app.route('/server/disable')
def disable():
    return api.disable()


@app.route('/mongo/status')
def checkMongo():
    return api.checkMongo()


if __name__ == '__main__':
    app.run(debug=True)
