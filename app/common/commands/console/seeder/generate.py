from datetime import datetime
import os
import config.enviroment as env

PRODUCT = env.ENVIRONMENT['PRODUCT']


class Generate:

    def __init__(self):
        self.__seedername = None

    @property
    def seedername(self):
        return self.__seedername

    @seedername.setter
    def seedername(self, value):
        self.__seedername = value

    def run(self):
        date = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        filename = f"{date}_{self.__seedername}_seed.py"

        f = open(f"{os.getcwd()}/database/seeders/{PRODUCT}/{filename}", "w")
        f.write(self.__content())
        f.close()

        self.__content()

        return filename

    def __content(self):
        f = open(f"{os.getcwd()}/app/common/commands/console/seeder/seeder_reference.txt", "r")
        migration_content = f.read()
        f.close()

        seedername_capitalized = ''.join(item.capitalize() for item in self.__seedername.split('_'))

        migration_content = migration_content.replace("__seedername__", self.__seedername)
        migration_content = migration_content.replace("__classname__", seedername_capitalized)
        migration_content = migration_content.replace("__queryset__", seedername_capitalized)

        return migration_content
