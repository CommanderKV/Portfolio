from .tools import *
from flask import *
import logfire

# Make the app
app = Blueprint("main", __name__)

# Start the scheduler
startBackgroundScheduler()

# GET: /robots.txt
@app.route("/robots.txt", methods=["GET"])
def robots():
    return send_from_directory("static", "robots.txt")

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

