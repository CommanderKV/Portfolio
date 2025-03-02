from ..models.User import Users
from flask import *
import logfire

app = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@app.before_request
@logfire.instrument("Checking if user is logged in")
def loginCheck():
    if "userId" not in session or "userName" not in session:
        logfire.info("User not logged in, redirecting to login")
        session.pop("userId", default=None)
        session.pop("userName", default=None)
        return redirect(url_for("login.login"))
    
    # Check the account
    if Users.query.filter_by(uid=session.get("userId")).first() is None:
        logfire.warn("User not found in database, logging out")
        session.pop("userId", default=None)
        session.pop("userName", default=None)
        return redirect(url_for("login.login"))
    
    logfire.info("User is logged in", user=session.get("userName"))
    return None

@app.route("/")
def home():
    username = session.get("userName")
    logfire.debug(f"Rendering {username}'s dashboard")
    return render_template("dashboard/home.html", username=username)