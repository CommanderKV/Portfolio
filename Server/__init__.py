from logging import FileHandler, WARNING
from flask_sqlalchemy import SQLAlchemy
from .getColors import run as getColors
from datetime import timedelta
from flask import Flask, render_template
import logfire
import sys
import os

# ---------------------------------
#   Get the environment variables
# ---------------------------------

# Check for the github api key
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")

if not GITHUB_API_KEY:
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
    
    # Logging errors
    #file_handler = FileHandler("error.log")
    #file_handler.setLevel(WARNING)
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    app.permanent_session_lifetime = timedelta(days=7)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    
    logfire.instrument_flask(app, exclude_urls="/static/*")

    # -------------------
    #   Database config
    # -------------------
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        from .models.Role import Roles
        from .models.User import Users
        db.create_all()
    
        # Check for roles
        roles = Roles.query.all()
        if not roles:
            db.session.add(Roles("admin"))
            db.session.add(Roles("user"))
            db.session.commit()
        
        if not any(role.name == "admin" for role in roles):
            db.session.add(Roles("admin"))
            db.session.commit()
        
        if not any(role.name == "user" for role in roles):
            db.session.add(Roles("user"))
            db.session.commit()

    # ----------------------------------
    #   Setup the controllers / routes
    # ----------------------------------
    from . import main
    from .controllers import login, dashboard
    app.register_blueprint(main.app)
    app.register_blueprint(login.app)
    app.register_blueprint(dashboard.app)
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("base.html", disableHeader=True, disableContact=True), 404

    # @app.errorhandler(500)
    # def internal_error(error):
    #     return render_template("base.html", disableHeader=True, disableContact=True), 500
    
    return app
