__author__ = 'sweemeng'
from wtforms import Form
from wtforms import SelectField


class ApprovalForm(Form):
    users = SelectField("Users", coerce=int)