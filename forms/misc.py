__author__ = 'sweemeng'
from wtforms import Form
from wtforms import StringField

# This is field that is shared by other field
# All these field is a list field
# To make life easy just enable it on edit view
class ContactForm(Form):
    id = StringField("id")
    type= StringField("Type")
    label = StringField("Label")
    value = StringField("Value")
    note = StringField("Note")


class LinkForm(Form):
    id = StringField("id")
    url = StringField("URL")
    note = StringField("Note")


class IdentifiersForm(Form):
    id = StringField("id")
    identifier = StringField("Identifier")
    scheme = StringField("Scheme")


class OtherNameForm(Form):
    id = StringField("id")
    name = StringField("Name")
    start_date = StringField("Start Date")
    end_date = StringField("End Date")
    note = StringField("Note")


class Area(Form):
    id = StringField("Id")
    name = StringField("Name")
    state = StringField("State")
