import datetime
import enum
from flask import g, Flask
from flask_migrate import Migrate
#from flask_sqlalchemy import SQLAlchemy

from common.config import conf
app = Flask(__name__)
