import datetime
import enum
from flask import g, Flask
from flask_migrate import Migrate
#from flask_sqlalchemy import SQLAlchemy

from common.config import conf
app = Flask(__name__)

class ChordsSite():
    def _init(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description

class ChordsIntrument():
    def _init(self, id):
        self.id = id

class ChordsVariable():
    def _init(self, id):
        self.id = id

class ChordsMeasurement():
    def _init(self, id):
        self.id = id
