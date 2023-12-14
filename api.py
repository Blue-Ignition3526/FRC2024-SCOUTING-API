from dotenv import load_dotenv
import os
from connection import MongoConnection
from matchDataBuilder import DataBuilder
from flask import jsonify
import requests


class Api:
    def __init__(self):
        # Setup MongoDB connection
        self.mongo = MongoConnection()
        self.mongo.test()
        self.db = self.mongo.db

        # Setup data builder
        self.dataBuilder = DataBuilder()

        # Setup TBA key
        load_dotenv()
        self.tbaKey = os.getenv('TBA_KEY')

        # Api variables
        self.apiStatus = True

    def status(self):
        return jsonify({'enabled': self.apiStatus}), 200

    def enable(self):
        self.apiStatus = True
        return jsonify({'message': 'API enabled'}), 201

    def disable(self):
        self.apiStatus = False
        return jsonify({'message': 'API disabled'}), 201

    def checkMongo(self):
        test = self.mongo.test()
        return jsonify({'mongo-status': test}), 200

    def generateEvent(self, eventKey):
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled'}), 400
        try:
            if self.db.Regional.count_documents({}, limit=1):  # Check if there is an entry in the Regional collection
                return jsonify({
                    'error': 'Event on progress, Invalid action'}), 400  # If there is, deny the request for creating a new event

            teams = requests.get(f'https://www.thebluealliance.com/api/v3/event/{eventKey}/teams',
                                 headers={'X-TBA-Auth-Key': self.tbaKey})  # Get the teams from the event

            event = requests.get(f'https://www.thebluealliance.com/api/v3/event/{eventKey}',
                                 headers={'X-TBA-Auth-Key': self.tbaKey})  # Get the event data from the event

            body = teams.json()  # Get the teams data from the request
            teams = []  # Create an empty list to store the teams
            for team in body:
                team['disabled'] = False
                teams.append({'team_number': team['team_number'], 'team_name': team['nickname']})  # Append the team data to the teams list
            body.append(event.json())  # Append the event data to the teams data

            result = self.db.Regional.insert_many(body)  # Insert the data into the Regional collection
            result2 = self.db.Teams.insert_many(teams)  # Insert the teams into the Teams collection

            if result.acknowledged and result2.acknowledged:  # If MongoDB acknowledged the insertion
                return jsonify({
                                   'message': f'Event {eventKey} successfully generated, {len(result.inserted_ids)} teams added'}), 201
            else:
                return jsonify({'error': f'Event {eventKey} could not be generated'}), 500

        except Exception as e:
            return jsonify({'error': f'Event {eventKey} does not exist or could not be generated'}), 500

    def clearEvent(self):
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled'}), 400
        try:
            # Check if there is an entry in the Regional collection
            if not self.db.Regional.count_documents({}, limit=1):
                # If there isn't, deny the request for clearing the event
                return jsonify({'error': 'No event on progress, Invalid action'}), 400

            result = self.db.Regional.delete_many({})

            if result.acknowledged:
                return jsonify({'message': f'{result.deleted_count} entries removed. Event cleared'}), 201
            else:
                return jsonify({'error': 'Event could not be cleared'}), 500

        except Exception as e:
            return jsonify({'error': 'Event could not be cleared'}), 500

    def getActiveEvent(self):
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled'}), 400
        try:
            teamCount = self.db.Regional.count_documents({})
            if teamCount == 0:
                return jsonify({'error': 'No event on progress'}), 400

            event = self.db.Regional.find_one({"first_event_code": {"$exists": True}})
            event['teamCount'] = teamCount - 1
            event['_id'] = str(event['_id'])

            if event:
                return jsonify(event), 200
            else:
                return jsonify({'error': 'Event could not be retrieved or does not exist'}), 500
        except Exception as e:
            return jsonify({'error': 'Event could not be retrieved'}), 500


    def addMatch(self, body):
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled'}), 400
        try:
            matchNumber = body['d'][0]
            teamNumber = body['d'][1]
            if self.db.Matches.count_documents({'matchNumber': matchNumber, 'teamNumber': teamNumber}, limit=1):
                return jsonify({'error': f'{teamNumber}\'s match {matchNumber} already exists'}), 400
            result = self.db.Matches.insert_one(self.dataBuilder.data(body[d]))
            if result.acknowledged:
                return jsonify({'message': f'{teamNumber}\'s match {matchNumber} succesfully added'}), 201
            else:
                return jsonify({'error': 'Match could not be added'}), 500
        except Exception as e:
            return jsonify({'error': 'Match could not be added'}), 500

    def addMultipleMatches(self, matchesData):
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled'}), 400
        try:
            matches = matchesData["d"]
            for match in matches:
                matchNumber = match[0]
                teamNumber = match[1]
                if self.db.Matches.count_documents({'matchNumber': matchNumber, 'teamNumber': teamNumber}, limit=1):
                    return jsonify({'error': f'{teamNumber}\'s match {matchNumber} already exists'}), 400
            result = self.db.Matches.insert_many([self.dataBuilder.data(match) for match in matches])
            if result.acknowledged:
                return jsonify({'message': f'{len(result.inserted_ids)} matches succesfully added'}), 201
            else:
                return jsonify({'error': 'Matches could not be added'}), 500
        except Exception as e:
            return jsonify({'error': 'Matches could not be added'}), 500

    def updateTeamMatch(self, identifier, matchData):
        return True

    def deleteTeamMatch(self, identifier):
        return True

    def deleteMatchNumber(self, matchNumber):
        return True