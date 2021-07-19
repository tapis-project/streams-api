import datetime
import enum
from flask import g, Flask
#from flask_cors import CORS
app = Flask(__name__)

#CORS(app,resources={r"/v3/streams/*": {"origins": "*"}},CORS_AUTOMATIC_OPTIONS=True)

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

class KapacitorTemplate:
    def __init__(self, id, type, script):
        self.id = id
        self.type = type
        self.script = script

class MetaTemplate:
    def __init__(self, template_id, type, script):
        self.template_id = template_id
        self.type = type
        self.script = script

class ChannelAlert:
    def __init__(self,id, message, condition,channel_id,action_taken, actor_id, execution_id):
        self.id = id
        self.message = message
        self.condition = condition
        self.channel_id = channel_id
        self.action_taken = action_taken
        self.actor_id = actor_id
        self.execution_id = execution_id

class ArchiveSystem:
    def __init__(self, updated_at, created_at, owner, system_id, path, frequency, range):
        self.type='archive'
        self.archive_type= 'system'
        self.updated_at = updated_at
        self.created_at = created_at
        self.owner = owner
        self.system_id = system_id
        self.path = dest_file_path
        self.frequency = frequency
        self.range = range

class ArchiveChords:
    def __init__(self, archive_type, updated_at, created_at, owner, chords_url, chords_email, chords_api_key, sites, instruments, variables):
        self.type='archive'
        self.archive_type= 'chords'
        self.updated_at = updated_at
        self.created_at = created_at
        self.owner = owner
        self.chords_url = chords_url
        self.chords_email = chords_email
        self.chords_api_key = chords_api_key
        self.sites = sites
        self.instruments= instruments
        self.variables = variables
