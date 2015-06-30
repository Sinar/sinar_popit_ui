__author__ = 'sweemeng'
from wtforms import Form
from wtforms import StringField
from wtforms import HiddenField

# This is field that is shared by other field
# All these field is a list field
# To make life easy just enable it on edit view
class ContactForm(Form):
    id = HiddenField("id")
    type= StringField("Type")
    label = StringField("Label")
    value = StringField("Value")
    note = StringField("Note")


class LinkForm(Form):
    id = HiddenField("id")
    url = StringField("URL")
    note = StringField("Note")


class IdentifiersForm(Form):
    id = HiddenField("id")
    identifier = StringField("Identifier")
    scheme = StringField("Scheme")


class OtherNameForm(Form):
    id = HiddenField("id")
    name = StringField("Name")
    start_date = StringField("Start Date")
    end_date = StringField("End Date")
    note = StringField("Note")


class Area(Form):
    id = StringField("Id")
    name = StringField("Name")
    state = StringField("State")
