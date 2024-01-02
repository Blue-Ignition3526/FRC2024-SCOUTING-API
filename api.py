from dotenv import load_dotenv
import os
from connection import MongoConnection
from matchDataBuilder import matchDataBuilder
from pitsDataBuilder import pitsDataBuilder
from flask import jsonify
import requests


class Api:
    def __init__(self):
        # Setup MongoDB connection
        self.mongo = MongoConnection()
        self.mongo.test()
        self.db = self.mongo.db

        # Setup data builder
        self.dataBuilder = matchDataBuilder()
        self.pitsDataBuilder = pitsDataBuilder()

        # Setup TBA key
        load_dotenv()
        self.tbaKey = os.getenv('TBA_KEY')

        # Api variables
        self.apiStatus = True

        # Delete variables
        self.delAttempts = 0

    def status(self):
        """
        A function that returns the status of the API
        :return: A JSON response that contains the status of the API and the status code
        """
        return jsonify({'enabled': self.apiStatus}), 200


    def enable(self):
        """
        A function that enables the API
        :return: A JSON response that contains the result of the operation and the status code
        """
        self.apiStatus = True
        return jsonify({'message': 'API enabled'}), 201


    def disable(self, password: str):
        """
        A function that disables the API
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        self.apiStatus = False
        return jsonify({'message': 'API disabled'}), 201


    def checkMongo(self):
        """
        A function that checks if the MongoDB connection is working
        :return: A JSON response that contains the result of the operation and the status code
        """
        test = self.mongo.test()
        return jsonify({'mongo-status': test}), 200


    def checkPassword(self, password: str):
        """
        A function that checks if the password is correct
        :param password: A string that contains the password
        :return: A boolean that indicates if the password is correct
        """
        if password == os.getenv('API_PASSWORD'):
            return True
        else:
            return False


    def generateEvent(self, eventKey: str):
        """
        A function that generates an event
        :param eventKey: A string that contains the event key, syntax: yyyy[EVENT_CODE], Ex: 2024mxto. The event key can be found in the TBA website
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            if self.db.Regional.count_documents({}, limit=1):  # Check if there is an entry in the Regional collection
                return jsonify({
                    'error': 'Event on progress, Invalid action', 'success': False}), 400  # If there is, deny the request for creating a new event

            teams = requests.get(f'https://www.thebluealliance.com/api/v3/event/{eventKey}/teams',
                                 headers={'X-TBA-Auth-Key': self.tbaKey})  # Get the teams from the event

            event = requests.get(f'https://www.thebluealliance.com/api/v3/event/{eventKey}',
                                 headers={'X-TBA-Auth-Key': self.tbaKey})  # Get the event data from the event

            regional = event.json()  # Get the event data from the request
            regional['teamCount'] = len(teams.json())  # Add the team count to the event data

            body = teams.json()  # Get the teams data from the request
            teams = []  # Create an empty list to store the teams
            for team in body:
                teams.append({'team_number': team['team_number'], 'team_name': team['nickname'], 'team_value': 0.00})  # Append the team data to the teams list
            body.append(regional)  # Append the event data to the teams data

            result = self.db.Regional.insert_many(body)  # Insert the data into the Regional collection
            result2 = self.db.Teams.insert_many(teams)  # Insert the teams into the Teams collection

            if result.acknowledged and result2.acknowledged:  # If MongoDB acknowledged the insertion
                return jsonify({'message': f'Event {eventKey} successfully generated, #{len(result2.inserted_ids)} teams added', 'success': True}), 201
            else:
                return jsonify({'error': f'Event {eventKey} could not be generated', 'success': False}), 500

        except Exception as e:
            return jsonify({'error': f'Event {eventKey} does not exist or could not be generated', 'success': False}), 500


    def clearEvent(self, password: str):
        """
        A function that clears the event
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        if self.delAttempts == 0:
            self.delAttempts += 1
            return jsonify({'message': 'Are you sure you want to clear the event? This action cannot be undone. Send the request again to confirm', 'success': True, 'tryAgain': True}), 200
        try:
            # Check if there is an entry in the Regional collection
            if not self.db.Regional.count_documents({}, limit=1):
                # If there isn't, deny the request for clearing the event
                return jsonify({'error': 'No event on progress, Invalid action', 'success': False}), 400

            regional = self.db.Regional.delete_many({})
            teams = self.db.Teams.delete_many({})
            # !TODO Enable the following deletes for production
            # matches = self.db.Matches.delete_many({})
            # pits = self.db.Pits.delete_many({})
            self.delAttempts = 0
            if regional.acknowledged:
                return jsonify({'message': f'{regional.deleted_count + teams.deleted_count} entries removed. Event cleared', 'success': True}), 201
            else:
                return jsonify({'error': 'Event could not be cleared', 'success': False}), 500

        except Exception as e:
            return jsonify({'error': 'Event could not be cleared', 'success': False}), 500


    def getActiveEvent(self):
        """
        A function that returns the active event
        :return: A JSON response that contains the active event or error code and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            teamCount = self.db.Regional.count_documents({})
            if teamCount == 0:
                return jsonify({'error': 'No event on progress', 'success': False}), 400

            event = self.db.Regional.find_one({"first_event_code": {"$exists": True}})
            event['teamCount'] = teamCount - 1
            event['_id'] = str(event['_id'])

            if event:
                return jsonify({'event': event, 'success': True}), 200
            else:
                return jsonify({'error': 'Event could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Event could not be retrieved', 'success': False}), 500


    def addMatch(self, data: dict):
        """
        A function that adds a match to the Matches Collection
        :param data: A dictionary that contains the data for the match inside the key 'd', stored as {'d': {matchData}}
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            matchNumber = data['d'][0]
            teamNumber = data['d'][1]
            if self.db.Matches.count_documents({'matchNumber': matchNumber, 'teamNumber': teamNumber}, limit=1):
                return jsonify({'error': f'{teamNumber}\'s match {matchNumber} already exists', 'success': False}), 400
            result = self.db.Matches.insert_one(self.dataBuilder.data(data['d']))
            if result.acknowledged:
                return jsonify({'message': f'{teamNumber}\'s match {matchNumber} successfully added', 'success': True}), 201
            else:
                return jsonify({'error': 'Match could not be added', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Match could not be added', 'success': False}), 500


    def addMultipleMatches(self, matchesData: dict):
        """
        A function that adds multiple matches to the Matches Collection
        :param matchesData: A dictionary that contains the data for the matches inside the key 'd', an array of dictionaries is stores, each dictionary represents a match, stored as {'d': [{matchData1},{matchData2}, ...]}
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            matches = matchesData["d"]
            for match in matches:
                matchNumber = match[0]
                teamNumber = match[1]
                if self.db.Matches.count_documents({'matchNumber': matchNumber, 'teamNumber': teamNumber}, limit=1):
                    return jsonify({'error': f'{teamNumber}\'s match {matchNumber} already exists', 'success': False}), 400
            result = self.db.Matches.insert_many([self.dataBuilder.data(match) for match in matches])
            if result.acknowledged:
                return jsonify({'message': f'{len(result.inserted_ids)} matches successfully added', 'success': True}), 201
            else:
                return jsonify({'error': 'Matches could not be added', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Matches could not be added', 'success': False}), 500


    def patchTeamMatch(self, identifier: dict, matchData: dict, password: str):
        """
        A function that patches certain values of a match
        :param identifier: A dictionary that contains the data to uniquely identify the match in this case the team number and the match number {'teamNumber': teamNumber, 'matchNumber': matchNumber}
        :param matchData: A dictionary that contains the data to be patched, key and value {'key': 'value', ...}
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            result = self.db.Matches.update_one(identifier, {"$set": matchData['d']})
            if result.matched_count > 0 and result.modified_count > 0:
                return jsonify({'message': f'Match successfully updated', 'success': True}), 201
            else:
                if result.matched_count == 0:
                    return jsonify({'error': 'Match could not be found', 'success': False}), 400
                if result.modified_count == 0:
                    return jsonify({'error': 'Match could not be updated', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Match could not be updated', 'success': False}), 500


    def updateTeamMatch(self, identifier: dict, matchData: dict, password: str):
        """
        A function that updates a match, replaces the entire match. Needs the same data as the addMatch function
        :param identifier: A dictionary that contains the data to uniquely identify the match in this case the team number and the match number {'teamNumber': teamNumber, 'matchNumber': matchNumber}
        :param matchData: A dictionary that contains the match data inside the key 'd', stored as {'d': {matchData}}
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            result = self.db.Matches.replace_one(identifier, {matchData['d']})
            if result.matched_count > 0 and result.modified_count > 0:
                return jsonify({'message': f'Match successfully updated', 'success': True}), 201
            else:
                if result.matched_count == 0:
                    return jsonify({'error': 'Match could not be found', 'success': False}), 400
                if result.modified_count == 0:
                    return jsonify({'error': 'Match could not be updated', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Match could not be updated', 'success': False}), 500

    def deleteTeamMatch(self, identifier: dict, password: str):
        """
        A function that deletes a match
        :param identifier: A dictionary that contains the data to uniquely identify the match in this case the team number and the match number {'teamNumber': teamNumber, 'matchNumber': matchNumber}
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            result = self.db.Matches.delete_one(identifier)
            if result.deleted_count > 0:
                return jsonify({'message': f'Match successfully deleted', 'success': True}), 201
            else:
                return jsonify({'error': 'Match could not be deleted or was not found', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Match could not be deleted', 'success': False}), 500

    def deleteMatchNumber(self, matchNumber: int, password: str):
        """
        A function that deletes all the matches with the specified match number
        :param matchNumber: A int that contains the match number
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            result = self.db.Matches.delete_many({"matchNumber": matchNumber})
            if result.deleted_count > 0:
                return jsonify({'message': f'Matches successfully deleted', 'success': True}), 201
            else:
                return jsonify({'error': 'Matches could not be deleted or was not found', 'success': False}), 400
        except Exception as e:
            return jsonify({'error': 'Matches could not be deleted', 'success': False}), 500


    def getMatch(self, identifier: dict):
        """
        A function that returns a match
        :param identifier: A dictionary that contains the data to uniquely identify the match in this case the team number and the match number {'teamNumber': teamNumber, 'matchNumber': matchNumber}
        :return: A JSON response that contains the match or error code and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            match = self.db.Matches.find_one(identifier)
            match['_id'] = str(match['_id'])

            if match:
                return jsonify({'match': match,'success': True}), 200
            else:
                return jsonify({'error': 'Match could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Match could not be retrieved', 'success': False}), 500


    def getMultipleMatches(self, identifier: dict):
        """
        A function that returns multiple matches
        :param identifier: A dictionary that contains the data to identify the matches  {'key1': value, 'key2': value, ...}
        :return: A JSON response that contains the matches or error code and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            matches = self.db.Matches.find(identifier)
            matchesList = []
            for match in matches:
                match['_id'] = str(match['_id'])
                matchesList.append(match)

            if matchesList:
                return jsonify({'matches': matchesList, 'success': True}), 200
            else:
                return jsonify({'error': 'Matches could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Matches could not be retrieved', 'success': False}), 500


    def getAllMatches(self):
        """
        A function that returns all the matches
        :return: A JSON response that contains the matches or error code and the status code
        """
        try:
            matches = self.db.Matches.find({})
            matchesList = []
            for match in matches:
                match['_id'] = str(match['_id'])
                matchesList.append(match)

            if matchesList:
                return jsonify({'matches': matchesList, 'success': True}), 200
            else:
                return jsonify({'error': 'Matches could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Matches could not be retrieved', 'success': False}), 500


    def addRobot(self, data: dict):
        """
        A function that adds a robot to the Pits collection
        :param data: A dictionary that contains the data for the robot inside the key 'd', stored as {'d': {robotData}}
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            teamNumber = data['d'][0]
            if self.db.Robots.count_documents({'teamNumber': teamNumber}, limit=1):
                return jsonify({'error': f'{teamNumber}\'s robot already exists', 'success': False}), 400
            result = self.db.Pits.insert_one(self.pitsDataBuilder.data(data['d']))
            if result.acknowledged:
                return jsonify({'message': f'{teamNumber}\'s robot successfully added', 'success': True}), 201
            else:
                return jsonify({'error': 'Robot could not be added', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Robot could not be added', 'success': False}), 500


    def addMultipleRobots(self, robotsData: dict):
        """
        A function that adds multiple robots to the Pits collection
        :param robotsData: A dictionary that contains the data for the robots inside the key 'd', an array of dictionaries is stores, each dictionary represents a robot, stored as {'d': [{robotData1},{robotData2}, ...]}
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            robots = robotsData["d"]
            for robot in robots:
                teamNumber = robot[0]
                if self.db.Robots.count_documents({'teamNumber': teamNumber}, limit=1):
                    return jsonify({'error': f'{teamNumber}\'s robot already exists', 'success': False}), 400
            result = self.db.Pits.insert_many([self.pitsDataBuilder.data(robot) for robot in robots])
            if result.acknowledged:
                return jsonify({'message': f'{len(result.inserted_ids)} robots successfully added', 'success': True}), 201
            else:
                return jsonify({'error': 'Robots could not be added', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Robots could not be added', 'success': False}), 500


    def patchRobot(self, identifier: dict, robotData: dict, password: str):
        """
        A function that patches certain values of a robot
        :param identifier: A dictionary that contains the data to uniquely identify the robot in this case the team number {'teamNumber': teamNumber}
        :param robotData: A dictionary that contains the data to be patched, key and value {'key': 'value', ...}
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            result = self.db.Pits.update_one(identifier, {"$set": robotData['d']})
            if result.matched_count > 0 and result.modified_count > 0:
                return jsonify({'message': f'Robot successfully updated', 'success': True}), 201
            else:
                if result.matched_count == 0:
                    return jsonify({'error': 'Robot could not be found', 'success': False}), 400
                if result.modified_count == 0:
                    return jsonify({'error': 'Robot could not be updated', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Robot could not be updated', 'success': False}), 500


    def updateRobot(self, identifier: dict, robotData: dict, password: str):
        """
        A function that updates a robot, replaces the entire robot. Needs the same data as the addRobot function
        :param identifier: A dictionary that contains the data to uniquely identify the robot in this case the team number {'teamNumber': teamNumber}
        :param robotData: A dictionary that contains the robot data inside the key 'd', stored as {'d': {robotData}}
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            result = self.db.Pits.replace_one(identifier, {robotData['d']})
            if result.matched_count > 0 and result.modified_count > 0:
                return jsonify({'message': f'Robot successfully updated', 'success': True}), 201
            else:
                if result.matched_count == 0:
                    return jsonify({'error': 'Robot could not be found', 'success': False}), 400
                if result.modified_count == 0:
                    return jsonify({'error': 'Robot could not be updated', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Robot could not be updated', 'success': False}), 500


    def deleteRobot(self, identifier: dict, password: str):
        """
        A function that deletes a robot
        :param identifier: A dictionary that contains the data to uniquely identify the robot in this case the team number {'teamNumber': teamNumber}
        :param password: The password previously set in the setup, stored in the .env file. Grants access to delete and update functions
        :return: A JSON response that contains the result of the operation and the status code
        """
        if not self.checkPassword(password):
            return jsonify({'error': 'Invalid password', 'success': False}), 400
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            result = self.db.Pits.delete_one(identifier)
            if result.deleted_count > 0:
                return jsonify({'message': f'Robot successfully deleted', 'success': True}), 201
            else:
                return jsonify({'error': 'Robot could not be deleted or was not found', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Robot could not be deleted', 'success': False}), 500


    def getRobot(self, identifier: dict):
        """
        A function that returns a robot
        :param identifier: A dictionary that contains the data to uniquely identify the robot in this case the team number {'teamNumber': teamNumber}
        :return: A JSON response that contains the robot or error code and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            robot = self.db.Pits.find_one(identifier)
            robot['_id'] = str(robot['_id'])

            if robot:
                return jsonify({'robot': robot,'success': True}), 200
            else:
                return jsonify({'error': 'Robot could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Robot could not be retrieved', 'success': False}), 500


    def getMultipleRobots(self, identifier: dict):
        """
        A function that returns multiple robots
        :param identifier: A dictionary that contains the data to identify the robots  {'key1': value, 'key2': value, ...}
        :return: A JSON response that contains the robots or error code and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            robots = self.db.Pits.find(identifier)
            robotsList = []
            for robot in robots:
                robot['_id'] = str(robot['_id'])
                robotsList.append(robot)

            if robotsList:
                return jsonify({'robots': robotsList, 'success': True}), 200
            else:
                return jsonify({'error': 'Robots could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Robots could not be retrieved', 'success': False}), 500


    def getAllRobots(self):
        """
        A function that returns all the robots
        :return: A JSON response that contains the robots or error code and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            robots = self.db.Pits.find({})
            robotsList = []
            for robot in robots:
                robot['_id'] = str(robot['_id'])
                robotsList.append(robot)

            if robotsList:
                return jsonify({'robots': robotsList, 'success': True}), 200
            else:
                return jsonify({'error': 'Robots could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Robots could not be retrieved', 'success': False}), 500

    # !TODO Change the function to be get completedMatches. Have the matches be sorted by timestamp in order to account for skipped matches. Also get the total amount of matches
    # https://www.thebluealliance.com/api/v3/event/2023mxmo/matches/simple
    def getRunningMatch(self):
        """
        A function that returns the running match
        :return: A JSON response that contains the running match or error code and the status code
        """
        if not self.apiStatus:
            return jsonify({'error': 'API is disabled', 'success': False}), 400
        try:
            pipeline = [
                {"$group": {"_id": "$matchNumber", "count": {"$sum": 1}}},
                {"$sort": {"_id": -1}},
                {"$limit": 1}
            ]

            result = self.db.Matches.aggregate(pipeline).next()
            if result:
                if result['count'] >= 3:
                    return jsonify({'matchNumber': result['_id']+1, 'success': True}), 200
                else:
                    return jsonify({'matchNumber': result['_id'], 'success': True}), 200
            else:
                return jsonify({'error': 'Match could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Match could not be retrieved', 'success': False}), 500


    def getAllTeams (self):
        """
        A function that returns all the teams
        :return: A JSON response that contains the teams or error code and the status code
        """
        try:
            teams = self.db.Teams.find({})
            teamsList = []
            for team in teams:
                team['_id'] = str(team['_id'])
                teamsList.append(team)

            if teamsList:
                return jsonify({'teams': teamsList, 'success': True}), 200
            else:
                return jsonify({'error': 'Teams could not be retrieved or does not exist', 'success': False}), 500
        except Exception as e:
            return jsonify({'error': 'Teams could not be retrieved', 'success': False}), 500