import datetime
import enum
from flask import g, Flask
from flask_migrate import Migrate
#from flask_sqlalchemy import SQLAlchemy

from common.config import conf
app = Flask(__name__)

class ChordsSite:
    def __init__(self,id, name, lat, long, elevation, description):
        self.id = id
        self.name = name
        self.lat = lat
        self.long = long
        self.elevation = elevation
        self.description = description

class ChordsIntrument():
    def __init__(self, id):
        self.id = id

class ChordsVariable():
    def ___init__(self, id):
        self.id = id

class ChordsMeasurement():
    def __init__(self):
