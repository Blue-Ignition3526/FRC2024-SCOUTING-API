import json

class pitsDataBuilder:
    def __init__(self):
        jsonData = open('keys.json', 'r')
        self.keys = json.load(jsonData)

    # 0: teamNumber, Integer (Ex: 1234)
    # 1: scouterId, Integer (Ex: 6)
    # 2: robotWeight: Dict (Ex: {'v': 100, 'u': Int (0 = Pounds, 1 = Kilograms)}) (Value, Units)
    # 3: robotSize: Dict (Ex: {'Size': [1 (Width), 2 (Length)], 'u': Int (0 = Inches, 1 = Centimeters)}) (Size, Units)
    # 4: driveTrain: Integer (0 = Mecanum, 1 = Omni, 2 = H-Drive, 3 = Swerve, 4 = Tank, 5 = Other)
    # 5: driveMotors: Integer (0 = CIM, 1 = Redlines, 2 = Neo 550, 3 = Neo, 4 = Neo Vortex, 5 = Falcon, 6 = Kraken, 7 = Other)
    # 6: vision: Boolean (True = Yes, False = No)

    def data (self, pitData: list):
        """
        A function that builds the data for the pit
        :param pitData: A list that contains the data for the pit
        :return: A dictionary that contains the data for the pit
        """
        processedData = {
            'teamNumber': pitData[0],
            'scouter': pitData[1],
            'robotWeight': pitData[2],
            'robotSize': pitData[3],
            'driveTrain': pitData[4],
            'driveMotors': pitData[5],
            'vision': pitData[6]
        }
        return processedData