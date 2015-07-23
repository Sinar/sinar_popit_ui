__author__ = 'sweemeng'
from base import BaseForm
from wtforms import StringField
from wtforms import FormField
from wtforms import FieldList
from misc import Area
from wtforms.validators import DataRequired

"""
{
  "id": "593",
  "label": "Kitchen assistant at Joe's Diner",
  "role": "Kitchen assistant",
  "person_id": "john-q-public",
  "organization_id": "abc-inc",
  "post_id": "abc-inc-kitchen-assistant",
  "start_date": "1970-01",
  "end_date": "1971-12-31",
  "contact_details": [
    {
      "type": "voice",
      "label": "Take-out and delivery",
      "value": "+1-800-555-0199",
      "note": "12pm to midnight"
    }
  ],
  "links": [
    {
      "url": "http://example.com/abc-inc/staff",
      "note": "ABC, Inc. staff page"
    }
  ]
}
"""
# Organization ID and Post ID can be derived with post ID
class MembershipForm(BaseForm):
    person = StringField("Person")
    person_id = StringField("Person ID", validators=[DataRequired()])
    organization = StringField("Organizations")
    organization_id = StringField("Organization ID")
    post = StringField("posts")
    post_id = StringField("Post ID")
    role = StringField("Role")
    area = FieldList(FormField(Area), max_entries=1)
    start_date = StringField("Start Date")
    end_date = StringField("End Date")


class MembershipEditForm(MembershipForm):
    id = StringField("PopIt ID")