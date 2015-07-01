__author__ = 'sweemeng'
from flask.ext.script import Manager
from flask.ext.security import Security, SQLAlchemyUserDatastore
from app import db
from app import app
from db import User
from db import Role

manager = Manager(app)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@manager.command
def create_user(email, password):
    db.create_all()
    if not user_datastore.find_user(email=email):
        user_datastore.create_user(email=email, password=password)
    db.session.commit()

@manager.command
def create_db():
    db.create_all()

if __name__ == "__main__":
    manager.run()
