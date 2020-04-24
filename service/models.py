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

class ChordsIntrument:
    def __init__(self, id, site_id, name, sensor_id, topic_category_id, description, display_points, plot_offset_value, plot_offset_units, sample_rate_seconds):
        self.id = id
        self.site_id=site_id
        self.name=name
        #self.sensor_id=sensor_id
        self.topic_category_id=topic_category_id
        self.description=description
        self.display_points=display_points
        self.plot_offset_value=plot_offset_value
        self.plot_offset_units=plot_offset_units
        self.sample_rate_seconds=sample_rate_seconds

class ChordsVariable:
    def __init__(self, id, instrument_id, name, shortname, commit):
        self.id = id
        self.instrument_id=instrument_id
        self.name=name
        self.shortname=shortname
        self.commit=commit

# class ChordsMeasurement():
#     def __init__(self):
