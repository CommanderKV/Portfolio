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



# Make the app
def create_app():
    app = Flask(__name__)
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    app.permanent_session_lifetime = timedelta(days=7)
    
    logfire.instrument_flask(app, exclude_urls="/static/*")
    
    # ----------
    #   Routes
    # ----------
    from . import main
    app.register_blueprint(main.app)
    
    # Geo location data by ip when the post request is made
    from .tools import getGeoData
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
    
    return app
