__author__ = 'sweemeng'
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import const

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = const.db_path
app.secret_key = const.secret_key
app.config["SECRET_KEY"] = const.secret_key
app.config["SECURITY_POST_LOGOUT_VIEW"] = "/login"
db = SQLAlchemy(app)