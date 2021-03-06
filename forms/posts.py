__author__ = 'sweemeng'
from wtforms import StringField
from wtforms import DateField
from wtforms import FormField
from wtforms import FieldList
from wtforms.validators import DataRequired
from base import BaseForm
from misc import Area
from wtforms.validators import Regexp
from wtforms.validators import Optional

"""
Form json schema in popolo
{
  "$schema": "http://json-schema.org/draft-03/schema#",
  "id": "http://www.popoloproject.com/schemas/post.json#",
  "title": "Post",
  "description": "A position that exists independent of the person holding it",
  "type": "object",
  "properties": {
    "id": {
      "description": "The post's unique identifier",
      "type": ["string", "null"]
    },
    "label": {
      "description": "A label describing the post",
      "type": ["string", "null"]
    },
    "other_label": {
      "description": "An alternate label",
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "role": {
      "description": "The function that the holder of the post fulfills",
      "type": ["string", "null"]
    },
    "organization_id": {
      "description": "The ID of the organization in which the post is held",
      "type": ["string", "null"]
    },
    "organization": {
      "description": "The organization in which the post is held",
      "$ref": "http://www.popoloproject.com/schemas/organization.json#"
    },
    "area_id": {
      "description": "The ID of the geographic area to which this post is related",
      "type": ["string", "null"]
    },
    "area": {
      "description": "The geographic area to which this post is related",
      "$ref": "http://www.popoloproject.com/schemas/area.json#"
    },
    "start_date": {
      "description": "The date on which the post was created",
      "type": ["string", "null"],
      "pattern": "^[0-9]{4}(-[0-9]{2}){0,2}$"
    },
    "end_date": {
      "description": "The date on which the post was eliminated",
      "type": ["string", "null"],
      "pattern": "^[0-9]{4}(-[0-9]{2}){0,2}$"
    },
    "contact_details": {
      "description": "Means of contacting the holder of the post",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/contact_detail.json#"
      }
    },
    "links": {
      "description": "URLs to documents about the post",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/link.json#"
      }
    },
    "memberships": {
      "description": "The memberships through which people hold the post in the organization",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/membership.json#"
      }
    },
    "created_at": {
      "description": "The time at which the resource was created",
      "type": ["string", "null"],
      "format": "date-time"
    },
    "updated_at": {
      "description": "The time at which the resource was last modified",
      "type": ["string", "null"],
      "format": "date-time"
    },
    "sources": {
      "description": "URLs to documents from which the resource is derived",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/link.json#"
      }
    }
  }
}

"""

# This is all the field we
class PostForm(BaseForm):
    label = StringField("Name")
    role = StringField("Role")
    organization = StringField("Organization")
    organization_id = StringField("Organization ID", validators=[DataRequired()])
    area = FieldList(FormField(Area), max_entries=1)
    start_date = StringField("Start Date", validators=[Regexp("^[0-9]{4}(-[0-9]{2}){0,2}$"), Optional()])
    end_date = StringField("End Date", validators=[Regexp("^[0-9]{4}(-[0-9]{2}){0,2}$"), Optional()])


class PostEditForm(PostForm):
    id = StringField("Post Id")

