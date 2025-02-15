from flask import *
import logfire

app = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@app.before_request
@logfire.instrument("Checking if user is logged in")
def loginCheck():
    if "userId" not in session or "oauthToken" not in session or "userName" not in session:
        logfire.info("User not logged in, redirecting to login")
        session.clear()
        return redirect(url_for("login.login"))
    
    logfire.info("User is logged in", user=session.get("userName"))
    return None

@app.route("/")
@logfire.instrument("GET /dashboard/")
def home():
    return render_template("base.html", header="")