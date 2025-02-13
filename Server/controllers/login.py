from flask import *
from ..models.User import Users
from .. import db, tools
import logfire

app = Blueprint("login", __name__)


@app.route("/login")
@logfire.instrument("GET /login")
def login():
    url = tools.getGithubCode()
    
    # User is logged in
    if url == True:
        return redirect(url_for("dashboard.home"))
    
    elif url == False:
        return login()
    
    return redirect(url)

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
        user = Users(githubOAuthToken=oauthToken)
        db.session.add(user)
        
        user.userName = userData["username"]
        user.name = userData["name"]
        user.email = userData["email"]
        
    # Update the user's token
    user.githubOAuthToken = oauthToken
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
        session.pop("userId", None)
        logfire.info("User logged out successfully")
    else:
        logfire.info("No user was logged in")
    return redirect(url_for("main.home"))