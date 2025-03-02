from logging import FileHandler, WARNING
from flask_sqlalchemy import SQLAlchemy
from .getColors import run as getColors
from datetime import timedelta
from flask import *
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
    from .tools import getGeoData
    app.register_blueprint(main.app)
    app.register_blueprint(login.app)
    app.register_blueprint(dashboard.app)
    
    # Geo location data by ip when the post request is made
    @app.before_request
    def geoLocation():
        if request.environ.get("HTTP_X_FORWARDED_FOR"):
            ip = request.environ.get("HTTP_X_FORWARDED_FOR")
        elif request.remote_addr:
            ip = request.remote_addr
        else:
            ip = None
            logfire.warn("Could not determine the IP address of the request")

        with logfire.span(f"Request from IP(s): {ip}", request=request.__dict__):
            if "geoData" in session.keys():
                logfire.debug("Using cached geo data", geoData=session.get("geoData"))
            else:
                if ip is not None:
                    if "," in ip:
                        data = []
                        for ip in ip.split(", ", 10):
                            # check if its more than an ip address
                            # 123.123.123.123 = 15 characters
                            if len(data) >= 15:
                                logfire.warn("Too many IP addresses in the request", ip=ip)
                                break

                            logfire.debug(f"Getting geo data for IP: {ip}")
                            geoData = getGeoData(ip)
                            
                            if geoData["status"] == "fail":
                                logfire.warn("Failed to get geo data", geoData=geoData)
                                continue
                            
                            data.append(geoData)
                        
                        logfire.debug("Saving geo data to session")
                        session["geoData"] = data
                    
                    else:
                        logfire.debug(f"Getting geo data for IP: {ip}")
                        geoData = getGeoData(ip)
                        
                        if geoData["status"] == "fail":
                            logfire.warn("Failed to get geo data", geoData=geoData)
                            return
                        
                        logfire.debug("Saving geo data to session")
                        session["geoData"] = geoData
                    
                    logfire.info("Obtained geo data", data=session.get("geoData"))


    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("base.html", disableHeader=True, disableContact=True), 404

    # @app.errorhandler(500)
    # def internal_error(error):
    #     return render_template("base.html", disableHeader=True, disableContact=True), 500
    
    return app
