from flask_sqlalchemy import SQLAlchemy
from .getColors import run as getColors
from flask_github import GitHub
from datetime import timedelta
from flask import Flask
import logfire
import sys
import os

# ---------------------------------
#   Get the environment variables
# ---------------------------------

# Check for the github api key
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
WEB3FORMS_KEY = os.getenv("WEB3FORMS_KEY")

if not GITHUB_API_KEY or not WEB3FORMS_KEY:
    print("Missing required environment variables.")
    logfire.fatal("Missing required environment variables.")
    sys.exit(1)

logfire.info("All required environment variables found.")

# ---- End of environment variables ----

# Entry point to routes and global vars
# Get the colors from the getColors.py file
COLORS = getColors()

# Setup default header for requests
HEADERS = {
    "Authorization": f"Bearer {GITHUB_API_KEY}"
}



db = SQLAlchemy()
github = None

# Make the app
def create_app():
    global db, github
    
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    app.permanent_session_lifetime = timedelta(days=7)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    
    app.config["GITHUB_CLIENT_ID"] = os.getenv("GITHUB_CLIENT_ID")
    app.config["GITHUB_CLIENT_SECRET"] = os.getenv("GITHUB_CLIENT_SECRET")
    github = GitHub(app)

    # -------------------
    #   Database config
    # -------------------
    db.init_app(app)

    from . import main
    from .controllers import login
    app.register_blueprint(main.app)
    app.register_blueprint(login.app)
    
    return app
