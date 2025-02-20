from flask import *
from ..models.User import Users
from .. import db, tools
import logfire

app = Blueprint("login", __name__)


@app.route("/login", methods=["GET"])
@logfire.instrument("GET /login")
def login():
    method = request.args.get("method")
    # /login?method=github
    if method == "github":
        url = tools.getGithubCode()
        
        # User is logged in
        if url is True:
            return redirect(url_for("dashboard.home"))
        
        elif url is False:
            return redirect(url_for("login.login"), code=302)
        
        return redirect(url)
    
    # /login?method=asdadd (invalid method)
    elif method is not None:
        logfire.warn("Invalid login method {method}", method=method)
        flash("Invalid login method", "error")
        return redirect(url_for("login.login"), code=302)
    
    # /login
    else:
        logfire.debug("Rendering login page")
        return render_template("login.html", disableHeader=True, disableContact=True)

@app.route("/github-callback")
@logfire.instrument("GET /github-callback")
def authorized():
    oauthToken = tools.getGithubAuthToken(request.args)

    # -- Get user data based off the auth token --
    if oauthToken is None:
        logfire.error("Authorization failed")
        return redirect(url_for("main.home"))
    
    userData = tools.getUserDetails(oauthToken)
    if userData is None:
        logfire.error("User data could not be retrieved")
        return redirect(url_for("main.home"))
    

    # -- User creation and login --
    logfire.debug("Checking if user exists", email=userData["email"])
    user: Users = Users.query.filter_by(email=userData["email"]).first()
    if user is None:
        logfire.debug("User not found, creating new user", token=oauthToken)
        user = Users(
            githubOAuthToken=oauthToken,
            userName=userData["username"],
            name=userData["name"],
            email=userData["email"]
        )
        db.session.add(user)
        
    # Update the user's token
    user.updateToken(oauthToken)
    db.session.commit()
    logfire.debug("User updated", user=user)
    
    session["oauthToken"] = oauthToken
    session["userId"] = user.id
    session["userName"] = user.userName
    session.permanent = True
    logfire.debug(
        "Saved user identifiers to session", 
        oauthToken=session.get("oauthToken"), 
        userId=session.get("userId"), 
        userName=session.get("userName")
    )
    
    logfire.info("Authorization successful")
    return redirect(url_for("dashboard.home"))

@app.route("/logout")
@logfire.instrument("GET /logout")
def logout():
    if session.get("userId"):
        session.clear()
        logfire.info("User logged out successfully")
    else:
        logfire.info("No user was logged in")
    return redirect(url_for("main.home"))