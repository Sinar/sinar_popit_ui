__author__ = 'sweemeng'
from base import BaseForm
from misc import ContactForm
from misc import OtherNameForm
from misc import IdentifiersForm
from misc import LinkForm
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import DateField
from wtforms import SelectField
from wtforms import FieldList
from wtforms import FormField


"""
{
  "$schema": "http://json-schema.org/draft-03/schema#",
  "id": "http://www.popoloproject.com/schemas/person.json#",
  "title": "Person",
  "description": "A real person, alive or dead",
  "type": "object",
  "properties": {
    "id": {
      "description": "The person's unique identifier",
      "type": ["string", "null"]
    },
    "name": {
      "description": "A person's preferred full name",
      "type": ["string", "null"]
    },
    "other_names": {
      "description": "Alternate or former names",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/other_name.json#"
      }
    },
    "identifiers": {
      "description": "Issued identifiers",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/identifier.json#"
      }
    },
    "family_name": {
      "description": "One or more family names",
      "type": ["string", "null"]
    },
    "given_name": {
      "description": "One or more primary given names",
      "type": ["string", "null"]
    },
    "additional_name": {
      "description": "One or more secondary given names",
      "type": ["string", "null"]
    },
    "honorific_prefix": {
      "description": "One or more honorifics preceding a person's name",
      "type": ["string", "null"]
    },
    "honorific_suffix": {
      "description": "One or more honorifics following a person's name",
      "type": ["string", "null"]
    },
    "patronymic_name": {
      "description": "One or more patronymic names",
      "type": ["string", "null"]
    },
    "sort_name": {
      "description": "A name to use in a lexicographically ordered list",
      "type": ["string", "null"]
    },
    "email": {
      "description": "A preferred email address",
      "type": ["string", "null"],
      "format": "email"
    },
    "gender": {
      "description": "A gender",
      "type": ["string", "null"]
    },
    "birth_date": {
      "description": "A date of birth",
      "type": ["string", "null"],
      "pattern": "^[0-9]{4}(-[0-9]{2}){0,2}$"
    },
    "death_date": {
      "description": "A date of death",
      "type": ["string", "null"],
      "pattern": "^[0-9]{4}(-[0-9]{2}){0,2}$"
    },
    "image": {
      "description": "A URL of a head shot",
      "type": ["string", "null"],
      "format": "uri"
    },
    "summary": {
      "description": "A one-line account of a person's life",
      "type": ["string", "null"]
    },
    "biography": {
      "description": "An extended account of a person's life",
      "type": ["string", "null"]
    },
    "national_identity": {
      "description": "A national identity",
      "type": ["string", "null"]
    },
    "contact_details": {
      "description": "Means of contacting the person",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/contact_detail.json#"
      }
    },
    "links": {
      "description": "URLs to documents about the person",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/link.json#"
      }
    },
    "memberships": {
      "description": "The person's memberships",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/membership.json#"
      }
    },
    "motions": {
      "description": "The person's motions",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/motion.json#"
      }
    },
    "speeches": {
      "description": "The person's speeches",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/speech.json#"
      }
    },
    "votes": {
      "description": "Votes cast by the person",
      "type": "array",
      "items": {
        "$ref": "http://www.popoloproject.com/schemas/vote.json#"
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
class PersonForm(BaseForm):
    language = StringField("Language")
    name = StringField("Name")
    other_names = FieldList(FormField(OtherNameForm), min_entries=1)
    identifiers = FieldList(FormField(IdentifiersForm))
    email = StringField("Email")
    gender = SelectField("Gender", choices=[("Male", "Male"), ("Female", "Female")])
    birth_date = StringField("Birth Date")
    death_date = StringField("Death Date")
    summary = StringField("Summary")
    biography = TextAreaField("Biography")
    contact_details = FieldList(FormField(ContactForm))
    links = FieldList(FormField(LinkForm))


class PersonEditForm(PersonForm):
    id = StringField("Person ID")