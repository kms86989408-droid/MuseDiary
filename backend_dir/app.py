from flask import Flask
from flask_login import LoginManager

def create_app(config_key):
    app = Flask(__name__)