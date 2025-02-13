from .controllers import login
from .tools import *
from flask import *
import regex as re
import logfire

# Make the app
app = Blueprint("main", __name__)

# Start the scheduler
startBackgroundScheduler()

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

# GET: /contact
@app.route("/contact", methods=["GET"])
@logfire.instrument("GET /contact")
def contact():
    logfire.debug("Rendering contact page")
    return render_template(
        "contact.html", 
        contact=CONTACT_INFO
    )

# GET: /skills
@app.route("/skills", methods=["GET"])
@logfire.instrument("GET /skills")
def skills():
    logfire.debug("Rendering skills page")
    return render_template(
        "skills.html",
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