__author__ = 'sweemeng'
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import const

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = const.db_path
app.secret_key = const.secret_key
app.config["SECRET_KEY"] = const.secret_key
app.config["SECURITY_POST_LOGOUT_VIEW"] = "/login"
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
app.config["SECURITY_POST_LOGIN_VIEW"] = "/organizations/edit"
app.config["SECURITY_UNAUTHORIZED_VIEW"] = "/login"
db = SQLAlchemy(app)