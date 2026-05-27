

class SeederMissingNameException(Exception):

    def __init__(self):
        super().__init__("Seeder name is required")
