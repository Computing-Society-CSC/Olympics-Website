from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import *
from flask_migrate import Migrate
import os
# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    # Initialize the Flask app
    webapp = Flask(__name__)

    # Configure the app (use your actual configuration here)
    webapp.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI  # Replace with your DB URI
    webapp.config['SECRET_KEY'] = SECRET_KEY

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = Credential_Path

    # Initialize the database with the app
    db.init_app(webapp)

    # Register routes (Blueprints)
    from .routes import bp  # Import the blueprint
    webapp.register_blueprint(bp, url_prefix='/')  # You can set a different URL prefix if needed


    from .models import Houses, Players
    with webapp.app_context():
        db.create_all()
        Houses.create_default_houses()
        Players.create_default_players()

    migrate = Migrate(webapp, db)

    return webapp
