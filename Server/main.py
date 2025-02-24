from .controllers import login
from .tools import *
from flask import *
import regex as re
import logfire
import time

# Make the app
app = Blueprint("main", __name__)

# Start the scheduler
startBackgroundScheduler()

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


# GET: /
@app.route("/", methods=["GET"])
def home():
    logfire.debug("Rendering home page")
    return render_template(
        "home.html", 
        projects=REPOS[:3], 
        account=GITHUB_ACCOUNT,
        contact=CONTACT_INFO
    )

# GET: /projects
@app.route("/projects", methods=["GET"])
def projects():
    logfire.debug("Rendering projects page")
    return render_template(
        "projects.html", 
        projects=REPOS,
        account=GITHUB_ACCOUNT,
        contact=CONTACT_INFO
    )

# GET: /projects/<repoName>
@app.route("/projects/<repoName>", methods=["GET"])
def projectDetails(repoName):
    # Get the details for the repository
    logfire.debug(f"Getting details for \"{repoName}\" repository", repoName=repoName)
    repo = None
    for repository in REPOS:
        if repository["title"] == repoName:
            repo = repository
            break
    
    # Repo was not found return a 404
    if repo is None:
        logfire.warn("Repository not found", repoName=repoName)
        return abort(404)
    
    # Render the project template
    logfire.debug("Rendering project details page")
    return render_template(
        "projectDetails.html",
        repo=repo,
        contact=CONTACT_INFO
    )

# GET: /about
@app.route("/about", methods=["GET"])
def about():
    logfire.debug("Rendering about page")
    return render_template(
        "about.html",
        contact=CONTACT_INFO
    )

# --------------
#   Api routes
# --------------
# GET: /api
@app.route("/api", methods=["GET"])
def api():
    data = {"message": "Hello, World!"}
    logfire.info("Returning API data", data=data)
    return jsonify(data)

