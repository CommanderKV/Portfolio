from apscheduler.schedulers.background import BackgroundScheduler
from . import HEADERS, COLORS, WEB3FORMS_KEY
from urllib.parse import urlencode
from .models.User import Users
from flask import *
import requests
import logfire
import copy
import os

@logfire.instrument("Getting geo data")
def getGeoData(ip: str): 
    url = "http://ip-api.com/json/" + ip
    logfire.debug("Sending request to get geo data", url=url)
    response = requests.get(url)
    if response.status_code == 200:
        logfire.debug("Returning", data=response.json())
        return response.json()
    else:
        logfire.debug("Failed to get data")
        return None

@logfire.instrument("Getting github code")
def getGithubCode() -> str | bool:
    """
    Returns the url to redirect the user to for 
    authorization or True if the user is logged in 
    and the user exists otherwise it returns False
    """
    if session.get("oauthToken"):
        if Users.query.filter_by(githubOAuthToken=session["oauthToken"]).first():
            logfire.info("User already logged in", session=session.__dict__)
            return True
        else:
            logfire.info("User not found in database. Logging out", session=session.__dict__)
            session.clear()
            return False
    
    else:
        logfire.info("User not logged in. Redirecting to github for authorization")
        params = {
            "client_id": os.getenv("GITHUB_CLIENT_ID"),
            "scope": "read:user,user:email"
        }
        url = "https://github.com/login/oauth/authorize?"
        url += urlencode(params)
        return url

@logfire.instrument("Getting github access token")
def getGithubAuthToken(args: dict[str, str]) -> str | None:
    # Check if the code is in the args
    if "code" not in args:
        logfire.error("Authorization failed code not in args", request=args)
        return None
    
    # Set code
    code = args.get("code")
    logfire.debug("Exchanging code for access token", code=code)
    
    # Get the access token
    params = {
        "code": code,
        "client_id": os.getenv("GITHUB_CLIENT_ID"),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET")
    }
    url = "https://github.com/login/oauth/access_token"
    response = requests.request(
        "POST",
        url,
        data=urlencode(params),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code != 200:
        logfire.error("Failed to get access token", response=response.json())
        return None
    
    oauthToken = response.json()
    if "access_token" not in oauthToken:
        logfire.error(f"Failed to get access token", response=oauthToken)
        return None

    oauthToken = oauthToken["access_token"]
    logfire.info("returning auth token", oauthToken=oauthToken)
    return oauthToken

@logfire.instrument("Getting user details from github")
def getUserDetails(authToken) -> dict[str, str] | None:
    # Get the username and name from github
    url = "https://api.github.com/user"
    logfire.debug("Sending request to get user details", url=url)
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {authToken}"
        }   
    )

    if response.status_code != 200:
        logfire.error("Failed to get user details returning None", response=response.json())
        return None
    
    data = response.json()
    logfire.debug("Data retrieved for name and username", data=data)
    
    logfire.debug("Filtering data")
    returnData = {
        "name": data["name"],
        "username": data["login"],
        "avatar": data["avatar_url"],
    }
    
    # Get the users email from github
    url = "https://api.github.com/user/emails"
    logfire.info("Getting users email", url=url)
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {authToken}"
        }
    )
    
    if response.status_code != 200:
        logfire.error("Failed to get user email returning None", response=response.json())
        return None
    
    emails = response.json()
    logfire.info("Emails retrieved", emails=emails)
    
    returnData["email"] = next((email["email"] for email in emails if email["primary"]), None)
    logfire.info("Returning user details", data=returnData)
    return returnData


# Get the images for repositories
@logfire.instrument("Getting images")
def getImages() -> dict[str, list[str]]:
    logfire.debug("Getting image paths")
    data: dict[str, list[str]] = {}
    
    # Get the current path
    currentPath = os.path.dirname(os.path.abspath(__file__))
    currentPath += "/static/images"
    logfire.debug("Current path", path=currentPath)
    
    # Find all the images in the directory
    for root, _, files in os.walk(currentPath):
        # Modify the images path so it can be referenced in 
        # the src attribute of the img tag
        directory = os.path.basename(root)
        files = [f"/static/images/{directory}/{file}" for file in files]
        logfire.debug("Found path", root=root, files=files)
        if root not in data.keys():
            data[root] = files
        else:
            data[root].extend(files)
    
    logfire.info("Returning image paths", data=data)
    return data

# Get the Github account details for the website
@logfire.instrument("Getting Github account details", extract_args=False)
def getGithubAccount(repositories: list[dict]=[]) -> dict:
    # Duplicate the repositories
    repos = copy.deepcopy(repositories)
    
    # Get the account details
    url = "https://api.github.com/users/CommanderKV"
    response = requests.get(
        url,
        headers=HEADERS
    )
    logfire.info(f"Getting account details", url=url)
    if response.status_code == 200:
        # Get the language data
        languages = {}
        total = 0
        logfire.info("Calculating language makeup")
        for repo in repos:
            for key in repo["languages"]:
                # Add to the language
                if key in languages:
                    languages[key]["percent"] += repo["languages"][key]["percent"]
                else:
                    languages[key] = repo["languages"][key]
                
                # Add to the total
                total += repo["languages"][key]["percent"]

        # Calculate the percentage
        for key in languages:
            languages[key]["percent"] = round((languages[key]["percent"] / total) * 100, 1)
            
        # Combine languages under 5% into "Other"
        other_languages = {"percent": 0, "color": "#ffffff"}
        for key in list(languages.keys()):
            if languages[key]["percent"] < 5:
                other_languages["percent"] += languages[key]["percent"]
                del languages[key]
        
        if other_languages["percent"] > 0:
            other_languages["percent"] = round(other_languages["percent"], 1)
            languages["Other"] = other_languages

        # Sort the languages by percentage
        languages = dict(sorted(languages.items(), key=lambda item: item[1]["percent"], reverse=True))
        
        # Return the data
        data = response.json()
        logfire.info("Returning account details")
        return {
            "name": data["name"],
            "username": data["login"],
            "avatar": data["avatar_url"],
            "followers": data["followers"],
            "following": data["following"],
            "repos": data["public_repos"],
            "url": data["html_url"],
            "bio": data["bio"],
            "languages": languages if languages else "Not available"
        }
        
    else:
        logfire.notice(
            "Error getting account details from Github.", 
            url=url,
            response=response
        )
        # Return default data
        return {
            "name": "Kyler Visser",
            "login": "CommanderKV",
            "avatar": "https://avatars.githubusercontent.com/u/62476048?v=4",
            "followers": 0,
            "following": 0,
            "repos": 0,
            "url": "https://www.github.com/CommanderKV",
            "bio": "Not available",
            "languages": "Not available"
        }

# Get the Github repositories for the website
@logfire.instrument("Getting Github repositories")
def getGithubRepos(limit: int=-1) -> list[dict]:
    # Get the github language makeup 
    # percentage and color for a repo
    def getRepoLanguageMakeup(url: str) -> dict:
        response = requests.get(
            url,
            headers=HEADERS
        )
        if response.status_code == 200:
            data: dict[str, int] = response.json()
            # Example data
            # {
            #   "JavaScript": 172770,
            #   "Python": 65226,
            #   "HTML": 25923,
            #   "CSS": 19182
            # }
            total = sum(data.values())
            result = {}
            for key in data:
                if key in COLORS:
                    if COLORS[key]["svg"] == "" or COLORS[key]["svg"] == None:
                        svg = None
                    else:
                        svg = COLORS[key]["svg"]
                result[key] = {
                    "percent": round((data[key] / total) * 100, 1),
                    "color": COLORS[key]["color"] if key in COLORS else "#000000",
                    "svg": svg
                }
            
            logfire.debug("Returning repo language makeup", url=url, languageMakeup=result)
            return result
        else:
            logfire.warn(
                "Error getting repo language makeup", 
                url=url, 
                response=response
            )
            return {}
        
    # Get the repos form github
    url = "https://api.github.com/users/CommanderKV/repos"
    response = requests.get(
        url,
        headers=HEADERS
    )
    logfire.info(f"Getting Github repos from {url}", url=url)
    if response.status_code == 200:
        repos = response.json()
        repos = sorted(repos, key=lambda x: x["updated_at"], reverse=True)
        
        # Get x amount of repos
        repos = repos[:limit] if limit > 0 else repos
        
        # Get the images of all the repos
        images = getImages()
        path = os.path.dirname(os.path.abspath(__file__))
        path += "/static/images"
        
        # Return the required data
        with logfire.span("Getting github repo language makeup"):
            data =  [
                {
                    "title": repo["name"],
                    "fullTitle": repo["full_name"],
                    "description": repo["description"] or "No description available",
                    "languages": getRepoLanguageMakeup(repo["languages_url"]),
                    "url": repo["html_url"],
                    "updatedAt": repo["updated_at"][:10],
                    "archived": repo["archived"],
                    "imageUrls": images.get(path + "/" + repo["name"], ["/static/images/github.png"])
                }
                for repo in repos
            ]
            
        logfire.info("Returning Github repos", repos=data)
        return data
    
    # Return an empty list since there was an error getting the repos
    else:
        logfire.notice(
            "Error getting Github repos.", 
            url=url, 
            response=response
        )
        return []

# Send an email to the web3forms API
@logfire.instrument("Sending email")
def sendEmail(email: str, body: str) -> bool:
    try:
        url = "https://api.web3forms.com/submit"
        requestBody = {
            "access_key": WEB3FORMS_KEY,
            "email": email,
            "subject": f"Portfolio contact attempt by {email}",
            "message": body
        }

        logfire.debug(
            "Sending email via web3forms API",
            url=url, 
            request=requestBody
        )
        response = requests.post(
            url=url,
            json=requestBody
        )
        
        if response.status_code == 200:
            logfire.info("Email sent successfully")
            return True
        else:
            logfire.error(f"Error sending email. Response code: {response.status_code}", response=response.json())
            return False
        
    except Exception as e:
        logfire.error(f"Error sending email: {e}")
        return False

# -----------------------------
#   Update the github account 
#    and profile every hour 
# -----------------------------
@logfire.instrument("Updating data")
def updateData():
    global REPOS, GITHUB_ACCOUNT
    
    REPOS = getGithubRepos()
    GITHUB_ACCOUNT = getGithubAccount(REPOS)

# Start the scheduler
def startBackgroundScheduler() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=updateData, trigger="interval", hours=1)
    scheduler.start()
    logfire.info("Scheduler started")

# ----------------------------------------
#   Setup constants so we can modify the 
#    values and not update every time a 
#               page loads.
# ----------------------------------------
REPOS = getGithubRepos()
GITHUB_ACCOUNT = getGithubAccount(REPOS)
CONTACT_INFO = {
    "email": "kylervisser@gmail.com",
    "phone": "+16479801335",
    "location": "https://www.google.com/maps/place/Toronto,+ON/",
    "socials": {
        "github": {
            "svg": """<svg class="white-fill" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 496 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M165.9 397.4c0 2-2.3 3.6-5.2 3.6-3.3 .3-5.6-1.3-5.6-3.6 0-2 2.3-3.6 5.2-3.6 3-.3 5.6 1.3 5.6 3.6zm-31.1-4.5c-.7 2 1.3 4.3 4.3 4.9 2.6 1 5.6 0 6.2-2s-1.3-4.3-4.3-5.2c-2.6-.7-5.5 .3-6.2 2.3zm44.2-1.7c-2.9 .7-4.9 2.6-4.6 4.9 .3 2 2.9 3.3 5.9 2.6 2.9-.7 4.9-2.6 4.6-4.6-.3-1.9-3-3.2-5.9-2.9zM244.8 8C106.1 8 0 113.3 0 252c0 110.9 69.8 205.8 169.5 239.2 12.8 2.3 17.3-5.6 17.3-12.1 0-6.2-.3-40.4-.3-61.4 0 0-70 15-84.7-29.8 0 0-11.4-29.1-27.8-36.6 0 0-22.9-15.7 1.6-15.4 0 0 24.9 2 38.6 25.8 21.9 38.6 58.6 27.5 72.9 20.9 2.3-16 8.8-27.1 16-33.7-55.9-6.2-112.3-14.3-112.3-110.5 0-27.5 7.6-41.3 23.6-58.9-2.6-6.5-11.1-33.3 2.6-67.9 20.9-6.5 69 27 69 27 20-5.6 41.5-8.5 62.8-8.5s42.8 2.9 62.8 8.5c0 0 48.1-33.6 69-27 13.7 34.7 5.2 61.4 2.6 67.9 16 17.7 25.8 31.5 25.8 58.9 0 96.5-58.9 104.2-114.8 110.5 9.2 7.9 17 22.9 17 46.4 0 33.7-.3 75.4-.3 83.6 0 6.5 4.6 14.4 17.3 12.1C428.2 457.8 496 362.9 496 252 496 113.3 383.5 8 244.8 8zM97.2 352.9c-1.3 1-1 3.3 .7 5.2 1.6 1.6 3.9 2.3 5.2 1 1.3-1 1-3.3-.7-5.2-1.6-1.6-3.9-2.3-5.2-1zm-10.8-8.1c-.7 1.3 .3 2.9 2.3 3.9 1.6 1 3.6 .7 4.3-.7 .7-1.3-.3-2.9-2.3-3.9-2-.6-3.6-.3-4.3 .7zm32.4 35.6c-1.6 1.3-1 4.3 1.3 6.2 2.3 2.3 5.2 2.6 6.5 1 1.3-1.3 .7-4.3-1.3-6.2-2.2-2.3-5.2-2.6-6.5-1zm-11.4-14.7c-1.6 1-1.6 3.6 0 5.9 1.6 2.3 4.3 3.3 5.6 2.3 1.6-1.3 1.6-3.9 0-6.2-1.4-2.3-4-3.3-5.6-2z"/></svg>""",
            "url": "https://www.github.com/CommanderKV"
        },
        "linkedin": {
            "svg": """<svg class="white-fill" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M416 32H31.9C14.3 32 0 46.5 0 64.3v383.4C0 465.5 14.3 480 31.9 480H416c17.6 0 32-14.5 32-32.3V64.3c0-17.8-14.4-32.3-32-32.3zM135.4 416H69V202.2h66.5V416zm-33.2-243c-21.3 0-38.5-17.3-38.5-38.5S80.9 96 102.2 96c21.2 0 38.5 17.3 38.5 38.5 0 21.3-17.2 38.5-38.5 38.5zm282.1 243h-66.4V312c0-24.8-.5-56.7-34.5-56.7-34.6 0-39.9 27-39.9 54.9V416h-66.4V202.2h63.7v29.2h.9c8.9-16.8 30.6-34.5 62.9-34.5 67.2 0 79.7 44.3 79.7 101.9V416z"/></svg>""",
            "url": "https://www.linkedin.com/in/kyler-visser-b94801227",
        },
        "instagram": {
            "svg": """<svg class="white-fill" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7-74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z"/></svg>""",
            "url": "https://www.instagram.com/commanderkvi/"
        },
    }
}
