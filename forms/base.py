__author__ = 'sweemeng'
from wtforms import Form
from wtforms import StringField
from wtforms import SelectField
import wtforms_json

wtforms_json.init()

class BaseForm(Form):
    pass