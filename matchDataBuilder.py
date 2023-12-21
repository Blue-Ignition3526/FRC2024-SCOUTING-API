import json

class matchDataBuilder:
    def __init__(self):
        jsonData = open('keys.json', 'r')
        self.keys = json.load(jsonData)

    # 0: matchNumber, Integer (Ex: 1)
    # 1: teamNumber, Integer (Ex: 1234)
    # 2: alliance, Boolean (True = Red, False = Blue)
    # 3: scouterId, Integer (Ex: 6)
    # 4: autoStarting: Integer (0 = Over Cable Bumper, 1 = Before Cable Bumper, 2 = Middle Charge Station, 3 = Station Wall)
    # 5: autoPreloaded: Integer (0 = None, 1 = Cube, 2 = Cone)
    # 6: autoMoved: Boolean (True = Moved, False = Did not move)
    # 7: autoConesLow: Integer (Ex: 3)
    # 8: autoConesMid: Integer (Ex: 2)
    # 9: autoConesHigh: Integer (Ex: 1)
    # 10: autoCubesLow: Integer (Ex: 3)
    # 11: autoCubesMid: Integer (Ex: 2)
    # 12: autoCubesHigh: Integer (Ex: 1)
    # 13: autoFailedPieces: Integer (Ex: 1)
    # 14: autoBalanced: Boolean (True = Balanced, False = Did not balance)
    # 15: autoNotes: String (Ex: "Notes")
    # 16: teleopConesLow: Integer (Ex: 3)
    # 17: teleopConesMid: Integer (Ex: 2)
    # 18: teleopConesHigh: Integer (Ex: 1)
    # 19: teleopCubesLow: Integer (Ex: 3)
    # 20: teleopCubesMid: Integer (Ex: 2)
    # 21: teleopCubesHigh: Integer (Ex: 1)
    # 22: teleopFailedPieces: Integer (Ex: 1)
    # 23: teleopEndGame: Integer (0 = None, 1 = Parked, 2 = Engaged, 3 = Balanced)
    def data(self, matchData: list):
        """
        A function that builds the data for the match
        :param matchData: A list that contains the data for the match
        :return: A dictionary that contains the data for the match
        """
        processedData = {
            'matchNumber': matchData[0],
            'teamNumber': matchData[1],
            'alliance': matchData[2],
            'scouter': matchData[3],
            'starting': matchData[4],
            'preloaded': matchData[5],
            'moved': matchData[6],
            'autoConesLow': matchData[7],
            'autoConesMid': matchData[8],
            'autoConesHigh': matchData[9],
            'autoCubesLow': matchData[10],
            'autoCubesMid': matchData[11],
            'autoCubesHigh': matchData[12],
            'autoFailedPieces': matchData[13],
            'autoBalanced': matchData[14],
            'autoNotes': matchData[15],
            'teleopConesLow': matchData[16],
            'teleopConesMid': matchData[17],
            'teleopConesHigh': matchData[18],
            'teleopCubesLow': matchData[19],
            'teleopCubesMid': matchData[20],
            'teleopCubesHigh': matchData[21],
            'teleopFailedPieces': matchData[22],
            'teleopEndGame': matchData[23]
        }
        return processedData

    def alliance(self, allianceBoolean: bool):
        """
        A function that returns the alliance as a string based on the boolean value
        :param allianceBoolean: A boolean value that determines the alliance color
        :return: A string that represents the alliance color
        """
        if allianceBoolean:
            return 'red'
        else:
            return 'blue'

    def scouter(self, scouter: int):
        """
        A function that returns the scouter name based on the scouter id
        :param scouter: An Int that represents the scouter id
        :return: The scouter name
        """
        if scouter > len(self.keys['scouters'])-1:
            raise IndexError('Scouter ID does not exist')
        return self.keys['scouters'][scouter]

    def starting(self, starting: int):
        """
        A function that returns the starting position based on the starting id
        :param starting: An Int that represents the starting id
        :return: The starting position
        """
        if starting > len(self.keys['starting'])-1:
            raise IndexError('Starting position does not exist')
        return self.keys['starting'][starting]

    def preloaded(self, preloaded: int):
        """
        A function that returns the preloaded position based on the preloaded id
        :param preloaded: An Int that represents the preloaded id
        :return: The preloaded position
        """
        if preloaded > len(self.keys['preloaded'])-1:
            raise IndexError('Preloaded piece does not exist')
        return self.keys['preloaded'][preloaded]