__author__ = 'sweemeng'
from base import BaseForm
from wtforms import StringField

from wtforms import FieldList
from wtforms import FormField
from misc import ContactForm
from misc import IdentifiersForm
from misc import OtherNameForm
from misc import LinkForm
from misc import Area
from wtforms.validators import DataRequired
from wtforms.validators import Regexp
from wtforms.validators import Optional


"""
{
  "id": "abc-inc",
  "name": "ABC, Inc.",
  "other_names": [
    {
      "name": "Bob's Diner",
      "start_date": "1950-01-01",
      "end_date": "1954-12-31"
    },
    {
      "name": "Joe's Diner",
      "start_date": "1955-01-01"
    },
    {
      "name": "Famous Joe's"
    }
  ],
  "identifiers": [
    {
      "identifier": "123456789",
      "scheme": "DUNS"
    },
    {
      "identifier": "US0123456789",
      "scheme": "ISIN"
    }
  ],
  "classification": "Corporation",
  "parent_id": "holding-company-corp",
  "founding_date": "1950-01-01",
  "dissolution_date": "2000-01-01",
  "image": "http://example.com/pub/photos/logo.gif",
  "contact_details": [
    {
      "type": "voice",
      "label": "Toll-free number",
      "value": "+1-800-555-0199",
      "note": "9am to 5pm weekdays"
    }
  ],
  "links": [
    {
      "url": "http://en.wikipedia.org/wiki/Joe's_Diner_(placeholder_name)",
      "note": "Wikipedia page"
    }
  ]
}
"""
class OrganizationForms(BaseForm):
    image = StringField("Image", validators=[Optional()])
    name = StringField("Name", validators=[DataRequired()])
    other_names = FieldList(FormField(OtherNameForm))
    identifiers = FieldList(FormField(IdentifiersForm))
    classification = StringField("Classification")
    parent_id = StringField("Parent ID")
    parent = StringField("Parent Organization")
    founding_date = StringField("Founding Date", validators=[Optional(), Regexp("^[0-9]{4}(-[0-9]{2}){0,2}$")])
    dissolution_date = StringField("Dissolution Date", validators=[Optional(), Regexp("^[0-9]{4}(-[0-9]{2}){0,2}$")])
    area = FieldList(FormField(Area), max_entries=1)
    contact_details = FieldList(FormField(ContactForm))
    links = FieldList(FormField(LinkForm))



class OrganizationEditForms(OrganizationForms):
    id = StringField("Organization ID")