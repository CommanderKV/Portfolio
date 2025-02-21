from .controllers import login
from .tools import *
from flask import *
import regex as re
import logfire

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
                    for ip in ip.split(", "):
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

# POST: /contact
@app.route("/api/contact", methods=["POST"])
def apiContact():
    # Get data from the request
    data: dict = request.json
    errors = []
    logfire.debug("Received contact form data", data=data)
    
    # Validating email data
    if not data.get("email"):
        errors.append("Email is required")
        logfire.warn("Email is required")
    elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", data.get("email")):
        errors.append("Invalid email format")
        logfire.warn("Invalid email format")
    
    # Validating message data
    if not data.get("message"):
        errors.append("Message is required")
        logfire.warn("Message is required")
    elif len(data.get("message")) < 10:
        errors.append("Message must be at least 10 characters")
        logfire.warn("Message must be at least 10 characters")
        
    # If there are errors then return them with a status code of 400
    if errors:
        logfire.warn("Errors in contact form", errors=errors)
        return jsonify({"success": False, "errors": errors}), 400
    
    # Send email
    if sendEmail(
        email=data.get("email"),
        body=data.get("message")
    ):
        # Message was sent successfully
        logfire.info("Message sent successfully")
        return jsonify({"success": True, "message": "Message sent successfully!"}), 200
    
    else:
        # Message failed to send
        logfire.warn("Failed to send message")
        return jsonify({"success": False, "message": "Failed to send message"}), 500