from base import BaseForm
from misc import LinkForm
from wtforms import FieldList
from wtforms import FormField
from wtforms import StringField
from wtforms import HiddenField
from wtforms.validators import URL


class CitationItemForm(BaseForm):
    id = HiddenField("id")
    url = StringField("URL")
    note = StringField("Note")


class CitationForm(BaseForm):
    citations = FieldList(FormField(CitationItemForm))