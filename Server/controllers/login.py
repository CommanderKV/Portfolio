from flask import *
from ..models.User import Users
from .. import db, github
import requests
import logfire

app = Blueprint("login", __name__)


@app.route("/login")
def login():
    return github.authorize(
        scope="read:user,user:email"
    )

@app.route("/github-callback")
@github.authorized_handler
def authorized(code):
    oauthToken = code or request.args.get("code")
    with logfire.span("Authorizing user"):
        nextUrl = request.args.get("next") or url_for("main.home")
        if oauthToken is None:
            logfire.error("Authorization failed", request=request, nextUrl=nextUrl)
            return redirect(nextUrl)

        user = Users.query.filter_by(githubOAuthToken=oauthToken).first()
        if user is None:
            userData = github.get("user")
            user_emails = github.get("user/emails")
            primary_email = next((email["email"] for email in user_emails if email["primary"]), None)

            user = Users(
                githubOAuthToken=oauthToken,
                userName=userData["login"],
                name=userData["name"],
                email=primary_email
            )
            db.session.add(user)
        
        user.githubOAuthToken = oauthToken
        db.session.commit()
        
        session["userId"] = user._id
        session["userName"] = user.userName
        session.permanent = True
        
        logfire.info("Authorization successful")
        return redirect(nextUrl)

@github.access_token_getter
def token_getter():
    user = Users.query.filter_by(_id=session.get("userId")).first() if session.get("userId") else None
    if user is not None:
        return user.githubOAuthToken

@app.route("/logout")
@logfire.instrument("Logging out user")
def logout():
    if session.get("userId"):
        session.pop("userId", None)
        logfire.info("User logged out successfully")
    else:
        logfire.info("No user was logged in")
    return redirect(url_for("main.home"))