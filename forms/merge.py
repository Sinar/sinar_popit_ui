__author__ = 'sweemeng'
from wtforms import Form
from wtforms import StringField
from wtforms import HiddenField
from wtforms.validators import DataRequired


class MergeForm(Form):
    source = StringField("Primary Person Name", validators=[DataRequired()])
    source_id = HiddenField("Primary Person Id", validators=[DataRequired()])
    target = StringField("Secondary Person Name", validators=[DataRequired()])
    target_id = HiddenField("Secondary Person Id", validators=[DataRequired()])