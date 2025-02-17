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
@app.route("/geo", methods=["POST"])
def geoLocation():
    if request.environ.get("HTTP_X_FORWARDED_FOR"):
        ip = request.environ.get("HTTP_X_FORWARDED_FOR")
    elif request.remote_addr:
        ip = request.remote_addr
    else:
        logfire.warn("Could not determine the IP address of the request")

    with logfire.span(f"Request from IP: {ip}", request=request.__dict__):
        if "geoData" in session.keys():
            logfire.debug("Using cached geo data", geoData=session.get("geoData"))
            return jsonify({"msg": "Using cached geo data"})
        
        geoData = getGeoData(ip)
        
        logfire.debug("Saving geo data to session")
        data = request.get_json()
        session["geoData"] = {
            "geoData": geoData,
            "siteData": {
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude")
            }
        }
        
        logfire.info("Obtained geo data", data=session.get("geoData"))
    
    return jsonify({"msg": "Geo data obtained"})


# GET: /
@app.route("/", methods=["GET"])
@logfire.instrument("GET /")
def home():
    logfire.debug("Rendering home page")
    return render_template(
        "home.html", 
        projects=REPOS[:3], 
        account=GITHUB_ACCOUNT,
        skills=getSkills(3),
        contact=CONTACT_INFO
    )

# GET: /projects
@app.route("/projects", methods=["GET"])
@logfire.instrument("GET /projects")
def projects():
    logfire.debug("Rendering projects page")
    return render_template(
        "projects.html", 
        projects=REPOS,
        account=GITHUB_ACCOUNT,
        contact=CONTACT_INFO
    )

# GET: /about
@app.route("/about", methods=["GET"])
@logfire.instrument("GET /about")
def about():
    logfire.debug("Rendering about page")
    return render_template(
        "about.html",
        skills=getSkills(),
        contact=CONTACT_INFO
    )

# --------------
#   Api routes
# --------------
# GET: /api
@app.route("/api", methods=["GET"])
@logfire.instrument("GET /api")
def api():
    data = {"message": "Hello, World!"}
    logfire.info("Returning API data", data=data)
    return jsonify(data)

# POST: /contact
@app.route("/api/contact", methods=["POST"])
@logfire.instrument("POST /api/contact")
def apiContact():
    # Get data from the request
    data: dict = request.json
    errors = {}
    logfire.debug("Received contact form data", data=data)
    
    # Validating name data
    if not data.get("name"):
        errors["name"] = "Name is required"
        logfire.warn("Name is required")
    elif len(data.get("name")) < 3:
        errors["name"] = "Must be at least 3 characters"
        logfire.warn("Name must be at least 3 characters")
    
    # Validating email data
    if not data.get("email"):
        errors["email"] = "Email is required"
        logfire.warn("Email is required")
    elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", data.get("email")):
        errors["email"] = "Invalid email format"
        logfire.warn("Invalid email format")
    
    # Validating message data
    if not data.get("message"):
        errors["message"] = "Message is required"
        logfire.warn("Message is required")
    elif len(data.get("message")) < 10:
        errors["message"] = "Must be at least 10 characters"
        logfire.warn("Message must be at least 10 characters")
        
    # If there are errors then return them with a status code of 400
    if errors:
        logfire.warn("Errors in contact form", errors=errors)
        return jsonify({"success": False, "errors": errors}), 400
    
    # Send email
    if sendEmail(
        name=data.get("name"),
        email=data.get("email"),
        body=data.get("message")
    ):
        # Message was sent successfully
        logfire.info("Message sent successfully")
        return jsonify({"success": True, "message": "Message sent successfully!"})
    
    else:
        # Message failed to send
        logfire.warn("Failed to send message")
        return jsonify({"success": False, "message": "Failed to send message"}), 500