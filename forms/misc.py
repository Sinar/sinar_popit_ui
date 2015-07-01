__author__ = 'sweemeng'
from wtforms import Form
from wtforms import StringField
from wtforms import HiddenField
from wtforms.validators import DataRequired
from wtforms.validators import Regexp
from wtforms.validators import Optional
from wtforms.validators import URL

# This is field that is shared by other field
# All these field is a list field
# To make life easy just enable it on edit view
class ContactForm(Form):
    id = HiddenField("id")
    type= StringField("Type", validators=[DataRequired()])
    label = StringField("Label", validators=[DataRequired()])
    value = StringField("Value", validators=[DataRequired()])
    note = StringField("Note")


class LinkForm(Form):
    id = HiddenField("id")
    url = StringField("URL", validators=[DataRequired(), URL()])
    note = StringField("Note")


class IdentifiersForm(Form):
    id = HiddenField("id")
    identifier = StringField("Identifier", validators=[DataRequired()])
    scheme = StringField("Scheme", validators=[DataRequired()])


class OtherNameForm(Form):
    id = HiddenField("id")
    name = StringField("Name", validators=[DataRequired()])
    start_date = StringField("Start Date", validators=[Optional(), Regexp("^[0-9]{4}(-[0-9]{2}){0,2}$")])
    end_date = StringField("End Date", validators=[Optional(), Regexp("^[0-9]{4}(-[0-9]{2}){0,2}$")])
    note = StringField("Note")


class Area(Form):
    id = StringField("Id", validators=[DataRequired()])
    name = StringField("Name")
    state = StringField("State")
