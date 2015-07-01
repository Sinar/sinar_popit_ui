__author__ = 'sweemeng'
import yaml
config = yaml.load(open("config.yaml"))
api_key= config["apikey"]
api_endpoint = config["api_endpoint"]
secret_key = config["secret_key"]
admin_name = config["admin_name"]
admin_pass = config["admin_pass"]
db_path = config["db_path"]