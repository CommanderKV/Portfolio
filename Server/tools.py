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
        
        # Return the required data
        with logfire.span("Getting github repo language makeup"):
            data =  [
                {
                    "title": repo["name"],
                    "description": repo["description"] or "No description available",
                    "languages": getRepoLanguageMakeup(repo["languages_url"]),
                    "url": repo["html_url"],
                    "imageUrl": "/static/images/github.png"
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

@logfire.instrument("Getting skills")
def getSkills(limit: int=-1) -> list[dict]:
    # Get the skills
    # SVGS from: https://devicon.dev
    skills = [
        {
            "name": "Database management",
            "description": "I have used SQL and MYSQL for database management in many different applications. (2 year experience)",
            "icons": [
                """<svg viewBox="0 0 128 128"><path fill="#00618A" d="M117.688 98.242c-6.973-.191-12.297.461-16.852 2.379-1.293.547-3.355.559-3.566 2.18.711.746.82 1.859 1.387 2.777 1.086 1.754 2.922 4.113 4.559 5.352 1.789 1.348 3.633 2.793 5.551 3.961 3.414 2.082 7.223 3.27 10.504 5.352 1.938 1.23 3.859 2.777 5.75 4.164.934.684 1.563 1.75 2.773 2.18v-.195c-.637-.812-.801-1.93-1.387-2.777l-2.578-2.578c-2.52-3.344-5.719-6.281-9.117-8.719-2.711-1.949-8.781-4.578-9.91-7.73l-.199-.199c1.922-.219 4.172-.914 5.949-1.391 2.98-.797 5.645-.59 8.719-1.387l4.164-1.187v-.793c-1.555-1.594-2.664-3.707-4.359-5.152-4.441-3.781-9.285-7.555-14.273-10.703-2.766-1.746-6.184-2.883-9.117-4.363-.988-.496-2.719-.758-3.371-1.586-1.539-1.961-2.379-4.449-3.566-6.738-2.488-4.793-4.93-10.023-7.137-15.066-1.504-3.437-2.484-6.828-4.359-9.91-9-14.797-18.687-23.73-33.695-32.508-3.195-1.867-7.039-2.605-11.102-3.57l-6.543-.395c-1.332-.555-2.715-2.184-3.965-2.977C16.977 3.52 4.223-3.312.539 5.672-1.785 11.34 4.016 16.871 6.09 19.746c1.457 2.012 3.32 4.273 4.359 6.539.688 1.492.805 2.984 1.391 4.559 1.438 3.883 2.695 8.109 4.559 11.695.941 1.816 1.98 3.727 3.172 5.352.727.996 1.98 1.438 2.18 2.973-1.227 1.715-1.297 4.375-1.984 6.543-3.098 9.77-1.926 21.91 2.578 29.137 1.383 2.223 4.641 6.98 9.117 5.156 3.918-1.598 3.043-6.539 4.164-10.902.254-.988.098-1.715.594-2.379v.199l3.57 7.133c2.641 4.254 7.324 8.699 11.297 11.699 2.059 1.555 3.68 4.242 6.344 5.152v-.199h-.199c-.516-.805-1.324-1.137-1.98-1.781-1.551-1.523-3.277-3.414-4.559-5.156-3.613-4.902-6.805-10.27-9.711-15.855-1.391-2.668-2.598-5.609-3.77-8.324-.453-1.047-.445-2.633-1.387-3.172-1.281 1.988-3.172 3.598-4.164 5.945-1.582 3.754-1.789 8.336-2.375 13.082-.348.125-.195.039-.398.199-2.762-.668-3.73-3.508-4.758-5.949-2.594-6.164-3.078-16.09-.793-23.191.59-1.836 3.262-7.617 2.18-9.316-.516-1.691-2.219-2.672-3.172-3.965-1.18-1.598-2.355-3.703-3.172-5.551-2.125-4.805-3.113-10.203-5.352-15.062-1.07-2.324-2.875-4.676-4.359-6.738-1.645-2.289-3.484-3.977-4.758-6.742-.453-.984-1.066-2.559-.398-3.566.215-.684.516-.969 1.191-1.191 1.148-.887 4.352.297 5.547.793 3.18 1.32 5.832 2.578 8.527 4.363 1.289.855 2.598 2.512 4.16 2.973h1.785c2.789.641 5.914.195 8.523.988 4.609 1.402 8.738 3.582 12.488 5.949 11.422 7.215 20.766 17.48 27.156 29.734 1.027 1.973 1.473 3.852 2.379 5.945 1.824 4.219 4.125 8.559 5.941 12.688 1.816 4.113 3.582 8.27 6.148 11.695 1.348 1.801 6.551 2.766 8.918 3.766 1.66.699 4.379 1.43 5.949 2.379 3 1.809 5.906 3.965 8.723 5.945 1.402.992 5.73 3.168 5.945 4.957zm-88.605-75.52c-1.453-.027-2.48.156-3.566.395v.199h.195c.695 1.422 1.918 2.34 2.777 3.566l1.98 4.164.199-.195c1.227-.867 1.789-2.25 1.781-4.363-.492-.52-.562-1.164-.992-1.785-.562-.824-1.66-1.289-2.375-1.98zm0 0"></path></svg>"""
            ]
        },
        {
            "name": "Web Development",
            "description": "I have developed web apps using HTML, CSS, and JavaScript. (2 year experience)",
            "icons": [
                """<svg viewBox="0 0 128 128"><path fill="#E44D26" d="M19.037 113.876L9.032 1.661h109.936l-10.016 112.198-45.019 12.48z"></path><path fill="#F16529" d="M64 116.8l36.378-10.086 8.559-95.878H64z"></path><path fill="#EBEBEB" d="M64 52.455H45.788L44.53 38.361H64V24.599H29.489l.33 3.692 3.382 37.927H64zm0 35.743l-.061.017-15.327-4.14-.979-10.975H33.816l1.928 21.609 28.193 7.826.063-.017z"></path><path fill="#fff" d="M63.952 52.455v13.763h16.947l-1.597 17.849-15.35 4.143v14.319l28.215-7.82.207-2.325 3.234-36.233.335-3.696h-3.708zm0-27.856v13.762h33.244l.276-3.092.628-6.978.329-3.692z"></path></svg>""", 
                """<svg viewBox="0 0 128 128"><path fill="#131313" d="M89.234 5.856H81.85l7.679 8.333v3.967H73.713v-4.645h7.678l-7.678-8.333V1.207h15.521v4.649zm-18.657 0h-7.384l7.679 8.333v3.967H55.055v-4.645h7.679l-7.679-8.333V1.207h15.522v4.649zm-18.474.19h-7.968v7.271h7.968v4.839H38.471V1.207h13.632v4.839z"></path><path fill="#1572B6" d="M27.613 116.706l-8.097-90.813h88.967l-8.104 90.798-36.434 10.102-36.332-10.087z"></path><path fill="#33A9DC" d="M64.001 119.072l29.439-8.162 6.926-77.591H64.001v85.753z"></path><path fill="#fff" d="M64 66.22h14.738l1.019-11.405H64V43.677h27.929l-.267 2.988-2.737 30.692H64V66.22z"></path><path fill="#EBEBEB" d="M64.067 95.146l-.049.014-12.404-3.35-.794-8.883H39.641l1.561 17.488 22.814 6.333.052-.015V95.146z"></path><path fill="#fff" d="M77.792 76.886L76.45 91.802l-12.422 3.353v11.588l22.833-6.328.168-1.882 1.938-21.647H77.792z"></path><path fill="#EBEBEB" d="M64.039 43.677v11.137H37.136l-.224-2.503-.507-5.646-.267-2.988h27.901zM64 66.221v11.138H51.753l-.223-2.503-.508-5.647-.267-2.988H64z"></path></svg>""", 
                """<svg viewBox="0 0 128 128"><path fill="#F0DB4F" d="M1.408 1.408h125.184v125.185H1.408z"></path><path fill="#323330" d="M116.347 96.736c-.917-5.711-4.641-10.508-15.672-14.981-3.832-1.761-8.104-3.022-9.377-5.926-.452-1.69-.512-2.642-.226-3.665.821-3.32 4.784-4.355 7.925-3.403 2.023.678 3.938 2.237 5.093 4.724 5.402-3.498 5.391-3.475 9.163-5.879-1.381-2.141-2.118-3.129-3.022-4.045-3.249-3.629-7.676-5.498-14.756-5.355l-3.688.477c-3.534.893-6.902 2.748-8.877 5.235-5.926 6.724-4.236 18.492 2.975 23.335 7.104 5.332 17.54 6.545 18.873 11.531 1.297 6.104-4.486 8.08-10.234 7.378-4.236-.881-6.592-3.034-9.139-6.949-4.688 2.713-4.688 2.713-9.508 5.485 1.143 2.499 2.344 3.63 4.26 5.795 9.068 9.198 31.76 8.746 35.83-5.176.165-.478 1.261-3.666.38-8.581zM69.462 58.943H57.753l-.048 30.272c0 6.438.333 12.34-.714 14.149-1.713 3.558-6.152 3.117-8.175 2.427-2.059-1.012-3.106-2.451-4.319-4.485-.333-.584-.583-1.036-.667-1.071l-9.52 5.83c1.583 3.249 3.915 6.069 6.902 7.901 4.462 2.678 10.459 3.499 16.731 2.059 4.082-1.189 7.604-3.652 9.448-7.401 2.666-4.915 2.094-10.864 2.07-17.444.06-10.735.001-21.468.001-32.237z"></path></svg>""",
                """<svg viewBox="0 0 128 128"><path fill="url(#a)" d="M0 64c0 18.593 28.654 33.667 64 33.667 35.346 0 64-15.074 64-33.667 0-18.593-28.655-33.667-64-33.667C28.654 30.333 0 45.407 0 64Z"></path><path fill="#777bb3" d="M64 95.167c33.965 0 61.5-13.955 61.5-31.167 0-17.214-27.535-31.167-61.5-31.167S2.5 46.786 2.5 64c0 17.212 27.535 31.167 61.5 31.167Z"></path><path d="M34.772 67.864c2.793 0 4.877-.515 6.196-1.53 1.306-1.006 2.207-2.747 2.68-5.175.44-2.27.272-3.854-.5-4.71-.788-.874-2.493-1.317-5.067-1.317h-4.464l-2.473 12.732zM20.173 83.547a.694.694 0 0 1-.68-.828l6.557-33.738a.695.695 0 0 1 .68-.561h14.134c4.442 0 7.748 1.206 9.827 3.585 2.088 2.39 2.734 5.734 1.917 9.935-.333 1.711-.905 3.3-1.7 4.724a15.818 15.818 0 0 1-3.128 3.92c-1.531 1.432-3.264 2.472-5.147 3.083-1.852.604-4.232.91-7.07.91h-5.724l-1.634 8.408a.695.695 0 0 1-.682.562z"></path><path fill="#fff" d="M34.19 55.826h3.891c3.107 0 4.186.682 4.553 1.089.607.674.723 2.097.331 4.112-.439 2.257-1.253 3.858-2.42 4.756-1.194.92-3.138 1.386-5.773 1.386h-2.786l2.205-11.342zm6.674-8.1H26.731a1.39 1.39 0 0 0-1.364 1.123L18.81 82.588a1.39 1.39 0 0 0 1.363 1.653h7.35a1.39 1.39 0 0 0 1.363-1.124l1.525-7.846h5.151c2.912 0 5.364-.318 7.287-.944 1.977-.642 3.796-1.731 5.406-3.237a16.522 16.522 0 0 0 3.259-4.087c.831-1.487 1.429-3.147 1.775-4.931.86-4.423.161-7.964-2.076-10.524-2.216-2.537-5.698-3.823-10.349-3.823zM30.301 68.557h4.471c2.963 0 5.17-.557 6.62-1.675 1.451-1.116 2.428-2.98 2.938-5.591.485-2.508.264-4.277-.665-5.308-.931-1.03-2.791-1.546-5.584-1.546h-5.036l-2.743 14.12m10.563-19.445c4.252 0 7.353 1.117 9.303 3.348 1.95 2.232 2.536 5.347 1.76 9.346-.322 1.648-.863 3.154-1.625 4.518-.764 1.366-1.76 2.614-2.991 3.747-1.468 1.373-3.097 2.352-4.892 2.935-1.794.584-4.08.875-6.857.875h-6.296l-1.743 8.97h-7.35l6.558-33.739h14.133"></path><path d="M69.459 74.577a.694.694 0 0 1-.682-.827l2.9-14.928c.277-1.42.209-2.438-.19-2.87-.245-.263-.979-.704-3.15-.704h-5.256l-3.646 18.768a.695.695 0 0 1-.683.56h-7.29a.695.695 0 0 1-.683-.826l6.558-33.739a.695.695 0 0 1 .682-.561h7.29a.695.695 0 0 1 .683.826L64.41 48.42h5.653c4.307 0 7.227.758 8.928 2.321 1.733 1.593 2.275 4.14 1.608 7.573l-3.051 15.702a.695.695 0 0 1-.682.56h-7.407z"></path><path fill="#fff" d="M65.31 38.755h-7.291a1.39 1.39 0 0 0-1.364 1.124l-6.557 33.738a1.39 1.39 0 0 0 1.363 1.654h7.291a1.39 1.39 0 0 0 1.364-1.124l3.537-18.205h4.682c2.168 0 2.624.463 2.641.484.132.14.305.795.019 2.264l-2.9 14.927a1.39 1.39 0 0 0 1.364 1.654h7.408a1.39 1.39 0 0 0 1.363-1.124l3.051-15.7c.715-3.686.103-6.45-1.82-8.217-1.836-1.686-4.91-2.505-9.398-2.505h-4.81l1.421-7.315a1.39 1.39 0 0 0-1.364-1.655zm0 1.39-1.743 8.968h6.496c4.087 0 6.907.714 8.457 2.14 1.553 1.426 2.017 3.735 1.398 6.93l-3.052 15.699h-7.407l2.901-14.928c.33-1.698.208-2.856-.365-3.474-.573-.617-1.793-.926-3.658-.926h-5.829l-3.756 19.327H51.46l6.558-33.739h7.292z"></path><path d="M92.136 67.864c2.793 0 4.878-.515 6.198-1.53 1.304-1.006 2.206-2.747 2.679-5.175.44-2.27.273-3.854-.5-4.71-.788-.874-2.493-1.317-5.067-1.317h-4.463l-2.475 12.732zM77.54 83.547a.694.694 0 0 1-.682-.828l6.557-33.738a.695.695 0 0 1 .682-.561H98.23c4.442 0 7.748 1.206 9.826 3.585 2.089 2.39 2.734 5.734 1.917 9.935a15.878 15.878 0 0 1-1.699 4.724 15.838 15.838 0 0 1-3.128 3.92c-1.53 1.432-3.265 2.472-5.147 3.083-1.852.604-4.232.91-7.071.91h-5.723l-1.633 8.408a.695.695 0 0 1-.683.562z"></path><path fill="#fff" d="M91.555 55.826h3.891c3.107 0 4.186.682 4.552 1.089.61.674.724 2.097.333 4.112-.44 2.257-1.254 3.858-2.421 4.756-1.195.92-3.139 1.386-5.773 1.386h-2.786l2.204-11.342zm6.674-8.1H84.096a1.39 1.39 0 0 0-1.363 1.123l-6.558 33.739a1.39 1.39 0 0 0 1.364 1.653h7.35a1.39 1.39 0 0 0 1.363-1.124l1.525-7.846h5.15c2.911 0 5.364-.318 7.286-.944 1.978-.642 3.797-1.731 5.408-3.238a16.52 16.52 0 0 0 3.258-4.086c.832-1.487 1.428-3.147 1.775-4.931.86-4.423.162-7.964-2.076-10.524-2.216-2.537-5.697-3.823-10.35-3.823zM87.666 68.557h4.47c2.964 0 5.17-.557 6.622-1.675 1.45-1.116 2.428-2.98 2.936-5.591.487-2.508.266-4.277-.665-5.308-.93-1.03-2.791-1.546-5.583-1.546h-5.035Zm10.563-19.445c4.251 0 7.354 1.117 9.303 3.348 1.95 2.232 2.537 5.347 1.759 9.346-.32 1.648-.862 3.154-1.624 4.518-.763 1.366-1.76 2.614-2.992 3.747-1.467 1.373-3.097 2.352-4.892 2.935-1.793.584-4.078.875-6.856.875h-6.295l-1.745 8.97h-7.35l6.558-33.739h14.133"></path><defs><radialGradient id="a" cx="0" cy="0" r="1" gradientTransform="matrix(84.04136 0 0 84.04136 38.426 42.169)" gradientUnits="userSpaceOnUse"><stop stop-color="#AEB2D5"></stop><stop offset=".3" stop-color="#AEB2D5"></stop><stop offset=".75" stop-color="#484C89"></stop><stop offset="1" stop-color="#484C89"></stop></radialGradient></defs></svg>""",
                """<svg viewBox="0 0 128 128"><path fill="#5fa04e" d="M114.313 55.254a.26.26 0 0 0-.145.044l-2.346 1.37a.3.3 0 0 0-.142.26v2.74c0 .116.055.204.142.262l2.346 1.368a.262.262 0 0 0 .29 0l2.342-1.368a.308.308 0 0 0 .145-.263V56.93a.303.303 0 0 0-.145-.26l-2.343-1.371a.26.26 0 0 0-.144-.044zM63.22 71.638c-.427 0-.852.104-1.214.308l-11.549 6.727a2.457 2.457 0 0 0-1.214 2.124V94.22c0 .874.462 1.69 1.214 2.128l3.04 1.746c1.476.728 1.997.726 2.662.726 2.17 0 3.415-1.339 3.415-3.64V81.935a.356.356 0 0 0-.348-.351h-1.474a.356.356 0 0 0-.35.351v13.248c0 1.019-1.069 2.04-2.776 1.167l-3.155-1.835c-.116-.058-.175-.206-.175-.322V80.767c0-.116.059-.26.175-.319l11.545-6.697c.087-.058.233-.058.349 0l11.548 6.697c.115.059.172.174.172.32v13.424c0 .145-.057.264-.172.322l-11.548 6.727c-.087.058-.233.058-.349 0l-2.951-1.779c-.087-.058-.203-.087-.29-.029-.81.466-.952.527-1.734.789-.174.058-.463.173.115.493l3.85 2.302c.376.203.78.319 1.214.319.434 0 .867-.115 1.214-.26l11.549-6.727a2.463 2.463 0 0 0 1.214-2.128V80.797c0-.874-.462-1.687-1.214-2.124l-11.549-6.727a2.488 2.488 0 0 0-1.214-.308Zm18.03 6.13a2.236 2.236 0 0 0-2.227 2.243 2.236 2.236 0 0 0 2.227 2.242c1.217 0 2.228-1.019 2.228-2.242a2.254 2.254 0 0 0-2.228-2.242zm-.03.379a1.86 1.86 0 0 1 1.883 1.864c0 1.02-.84 1.894-1.882 1.894-1.012 0-1.852-.846-1.852-1.894s.869-1.864 1.852-1.864zm-.809.611v2.562h.494v-1.016h.434c.174 0 .231.058.26.203 0 .03.086.67.086.786h.52c-.058-.116-.087-.466-.116-.67-.028-.32-.056-.553-.404-.582.174-.059.463-.146.463-.612 0-.67-.58-.67-.868-.67zm.435.408h.404c.146 0 .376 0 .376.349 0 .116-.056.351-.376.351h-.405zm-14.47 2.01c-3.3 0-5.268 1.398-5.268 3.757 0 2.534 1.968 3.23 5.123 3.551 3.79.379 4.08.933 4.08 1.69 0 1.31-1.044 1.864-3.475 1.864-3.068 0-3.733-.758-3.965-2.301 0-.175-.142-.29-.316-.29H61.05a.35.35 0 0 0-.346.349c0 1.98 1.041 4.31 6.107 4.31 3.645 0 5.758-1.458 5.758-4.02 0-2.505-1.68-3.174-5.238-3.64-3.59-.466-3.965-.728-3.965-1.572 0-.699.318-1.63 2.98-1.63 2.373 0 3.269.525 3.617 2.126a.34.34 0 0 0 .319.26h1.533c.088 0 .175-.057.234-.115a.476.476 0 0 0 .085-.263c-.231-2.795-2.053-4.077-5.758-4.077z"></path><path fill="#333" d="M86.072 24.664a.71.71 0 0 0-.352.089.755.755 0 0 0-.375.638V44.32c0 .174-.09.35-.263.466a.549.549 0 0 1-.52 0l-3.066-1.775a1.486 1.486 0 0 0-1.478 0L67.75 50.146a1.48 1.48 0 0 0-.753 1.279v14.24c0 .524.29 1.02.753 1.282l12.27 7.135a1.486 1.486 0 0 0 1.477 0l12.269-7.135c.463-.262.753-.758.753-1.282V30.168c0-.553-.29-1.05-.753-1.311l-7.32-4.104a.836.836 0 0 0-.373-.089zM13.687 42.43c-.231 0-.462.084-.664.2L.753 49.739A1.493 1.493 0 0 0 0 51.047l.03 19.102c0 .263.143.525.375.642a.656.656 0 0 0 .724 0l7.294-4.193c.463-.262.75-.758.75-1.282v-8.94c0-.524.29-1.02.754-1.282l3.096-1.805c.231-.146.493-.204.753-.204s.521.058.724.204l3.096 1.805c.463.262.753.758.753 1.282v8.94c0 .524.288 1.02.75 1.282l7.236 4.193a.704.704 0 0 0 .753 0 .724.724 0 0 0 .376-.642V51.047c0-.524-.29-1.02-.754-1.283L14.47 42.63a1.763 1.763 0 0 0-.664-.201Zm100.667.21c-.253 0-.504.066-.736.198l-12.272 7.131c-.463.262-.75.758-.75 1.283v14.24c0 .524.287 1.02.75 1.282l12.184 6.987a1.43 1.43 0 0 0 1.447 0l7.38-4.133a.724.724 0 0 0 .375-.642.724.724 0 0 0-.375-.64L110.03 61.21a.76.76 0 0 1-.375-.641v-4.456a.72.72 0 0 1 .375-.64l3.85-2.214a.705.705 0 0 1 .753 0l3.846 2.213a.762.762 0 0 1 .378.641v3.495c0 .263.144.525.375.641a.704.704 0 0 0 .754 0l7.291-4.28a1.46 1.46 0 0 0 .724-1.283v-3.465c0-.524-.29-1.017-.724-1.28l-12.184-7.104a1.499 1.499 0 0 0-.738-.198zM80.757 53.274c.065 0 .131.015.19.045l4.194 2.446c.116.058.175.202.175.319v4.892c0 .146-.059.264-.175.322l-4.195 2.446a.431.431 0 0 1-.378 0l-4.195-2.446c-.116-.058-.175-.205-.175-.322v-4.892c0-.146.06-.261.175-.32l4.195-2.445a.425.425 0 0 1 .19-.045z"></path><path fill="url(#a)" d="M47.982 42.893a1.484 1.484 0 0 0-1.476 0L34.322 49.97a1.456 1.456 0 0 0-.724 1.281v14.181c0 .525.29 1.02.724 1.282l12.184 7.076a1.484 1.484 0 0 0 1.476 0l12.183-7.076c.463-.262.724-.757.724-1.282V51.251c0-.524-.29-1.02-.724-1.281z"></path><path fill="url(#b)" d="m60.194 49.97-12.241-7.077a1.996 1.996 0 0 0-.376-.145L33.859 66.364c.116.146.26.262.405.35l12.242 7.076c.347.204.752.262 1.128.145l12.879-23.703a.905.905 0 0 0-.319-.262z"></path><path fill="url(#c)" d="M60.194 66.713c.348-.204.608-.553.724-.932l-13.4-23.063c-.346-.058-.723-.029-1.041.175L34.322 49.94l13.11 24.053c.173-.029.376-.087.55-.175z"></path><defs><linearGradient id="a" x1="34.513" x2="27.157" y1="15.535" y2="30.448" gradientTransform="translate(0 24.664) scale(1.51263)" gradientUnits="userSpaceOnUse"><stop stop-color="#3F873F"></stop><stop offset=".33" stop-color="#3F8B3D"></stop><stop offset=".637" stop-color="#3E9638"></stop><stop offset=".934" stop-color="#3DA92E"></stop><stop offset="1" stop-color="#3DAE2B"></stop></linearGradient><linearGradient id="b" x1="30.009" x2="50.533" y1="23.359" y2="8.288" gradientTransform="translate(0 24.664) scale(1.51263)" gradientUnits="userSpaceOnUse"><stop offset=".138" stop-color="#3F873F"></stop><stop offset=".402" stop-color="#52A044"></stop><stop offset=".713" stop-color="#64B749"></stop><stop offset=".908" stop-color="#6ABF4B"></stop></linearGradient><linearGradient id="c" x1="21.917" x2="40.555" y1="22.261" y2="22.261" gradientTransform="translate(0 24.664) scale(1.51263)" gradientUnits="userSpaceOnUse"><stop offset=".092" stop-color="#6ABF4B"></stop><stop offset=".287" stop-color="#64B749"></stop><stop offset=".598" stop-color="#52A044"></stop><stop offset=".862" stop-color="#3F873F"></stop></linearGradient></defs></svg>"""
            ]
        },
        {
            "name": "Python Development",
            "description": "Python was my first language that I started developing in and I feel fairly confident in my abilities with it. (5 year experience)",
            "icons": [
                """<svg viewBox="0 0 128 128"><linearGradient id="python-original-a" gradientUnits="userSpaceOnUse" x1="70.252" y1="1237.476" x2="170.659" y2="1151.089" gradientTransform="matrix(.563 0 0 -.568 -29.215 707.817)"><stop offset="0" stop-color="#5A9FD4"></stop><stop offset="1" stop-color="#306998"></stop></linearGradient><linearGradient id="python-original-b" gradientUnits="userSpaceOnUse" x1="209.474" y1="1098.811" x2="173.62" y2="1149.537" gradientTransform="matrix(.563 0 0 -.568 -29.215 707.817)"><stop offset="0" stop-color="#FFD43B"></stop><stop offset="1" stop-color="#FFE873"></stop></linearGradient><path fill="url(#python-original-a)" d="M63.391 1.988c-4.222.02-8.252.379-11.8 1.007-10.45 1.846-12.346 5.71-12.346 12.837v9.411h24.693v3.137H29.977c-7.176 0-13.46 4.313-15.426 12.521-2.268 9.405-2.368 15.275 0 25.096 1.755 7.311 5.947 12.519 13.124 12.519h8.491V67.234c0-8.151 7.051-15.34 15.426-15.34h24.665c6.866 0 12.346-5.654 12.346-12.548V15.833c0-6.693-5.646-11.72-12.346-12.837-4.244-.706-8.645-1.027-12.866-1.008zM50.037 9.557c2.55 0 4.634 2.117 4.634 4.721 0 2.593-2.083 4.69-4.634 4.69-2.56 0-4.633-2.097-4.633-4.69-.001-2.604 2.073-4.721 4.633-4.721z" transform="translate(0 10.26)"></path><path fill="url(#python-original-b)" d="M91.682 28.38v10.966c0 8.5-7.208 15.655-15.426 15.655H51.591c-6.756 0-12.346 5.783-12.346 12.549v23.515c0 6.691 5.818 10.628 12.346 12.547 7.816 2.297 15.312 2.713 24.665 0 6.216-1.801 12.346-5.423 12.346-12.547v-9.412H63.938v-3.138h37.012c7.176 0 9.852-5.005 12.348-12.519 2.578-7.735 2.467-15.174 0-25.096-1.774-7.145-5.161-12.521-12.348-12.521h-9.268zM77.809 87.927c2.561 0 4.634 2.097 4.634 4.692 0 2.602-2.074 4.719-4.634 4.719-2.55 0-4.633-2.117-4.633-4.719 0-2.595 2.083-4.692 4.633-4.692z" transform="translate(0 10.26)"></path><radialGradient id="python-original-c" cx="1825.678" cy="444.45" r="26.743" gradientTransform="matrix(0 -.24 -1.055 0 532.979 557.576)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#B8B8B8" stop-opacity=".498"></stop><stop offset="1" stop-color="#7F7F7F" stop-opacity="0"></stop></radialGradient><path opacity=".444" fill="url(#python-original-c)" d="M97.309 119.597c0 3.543-14.816 6.416-33.091 6.416-18.276 0-33.092-2.873-33.092-6.416 0-3.544 14.815-6.417 33.092-6.417 18.275 0 33.091 2.872 33.091 6.417z"></path></svg>"""
            ]
        },
        {
            "name": "ASP.NET Development",
            "description": "I've developed web applications using ASP.NET and C# (1 year experience).",
            "icons": [
                """<svg viewBox="0 0 128 128"><path fill="#9B4F96" d="M115.4 30.7L67.1 2.9c-.8-.5-1.9-.7-3.1-.7-1.2 0-2.3.3-3.1.7l-48 27.9c-1.7 1-2.9 3.5-2.9 5.4v55.7c0 1.1.2 2.4 1 3.5l106.8-62c-.6-1.2-1.5-2.1-2.4-2.7z"></path><path fill="#68217A" d="M10.7 95.3c.5.8 1.2 1.5 1.9 1.9l48.2 27.9c.8.5 1.9.7 3.1.7 1.2 0 2.3-.3 3.1-.7l48-27.9c1.7-1 2.9-3.5 2.9-5.4V36.1c0-.9-.1-1.9-.6-2.8l-106.6 62z"></path><path fill="#fff" d="M85.3 76.1C81.1 83.5 73.1 88.5 64 88.5c-13.5 0-24.5-11-24.5-24.5s11-24.5 24.5-24.5c9.1 0 17.1 5 21.3 12.5l13-7.5c-6.8-11.9-19.6-20-34.3-20-21.8 0-39.5 17.7-39.5 39.5s17.7 39.5 39.5 39.5c14.6 0 27.4-8 34.2-19.8l-12.9-7.6zM97 66.2l.9-4.3h-4.2v-4.7h5.1L100 51h4.9l-1.2 6.1h3.8l1.2-6.1h4.8l-1.2 6.1h2.4v4.7h-3.3l-.9 4.3h4.2v4.7h-5.1l-1.2 6h-4.9l1.2-6h-3.8l-1.2 6h-4.8l1.2-6h-2.4v-4.7H97zm4.8 0h3.8l.9-4.3h-3.8l-.9 4.3z"></path></svg>"""
            ]
        },
        {
            "name": "Mobile app development",
            "description": "I have developed mobile apps using Java and Kotlin for Android. (<1 year experience)",
            "icons": [
                """<svg viewBox="0 0 128 128"><path fill="#0074BD" d="M47.617 98.12s-4.767 2.774 3.397 3.71c9.892 1.13 14.947.968 25.845-1.092 0 0 2.871 1.795 6.873 3.351-24.439 10.47-55.308-.607-36.115-5.969zm-2.988-13.665s-5.348 3.959 2.823 4.805c10.567 1.091 18.91 1.18 33.354-1.6 0 0 1.993 2.025 5.132 3.131-29.542 8.64-62.446.68-41.309-6.336z"></path><path fill="#EA2D2E" d="M69.802 61.271c6.025 6.935-1.58 13.17-1.58 13.17s15.289-7.891 8.269-17.777c-6.559-9.215-11.587-13.792 15.635-29.58 0 .001-42.731 10.67-22.324 34.187z"></path><path fill="#0074BD" d="M102.123 108.229s3.529 2.91-3.888 5.159c-14.102 4.272-58.706 5.56-71.094.171-4.451-1.938 3.899-4.625 6.526-5.192 2.739-.593 4.303-.485 4.303-.485-4.953-3.487-32.013 6.85-13.743 9.815 49.821 8.076 90.817-3.637 77.896-9.468zM49.912 70.294s-22.686 5.389-8.033 7.348c6.188.828 18.518.638 30.011-.326 9.39-.789 18.813-2.474 18.813-2.474s-3.308 1.419-5.704 3.053c-23.042 6.061-67.544 3.238-54.731-2.958 10.832-5.239 19.644-4.643 19.644-4.643zm40.697 22.747c23.421-12.167 12.591-23.86 5.032-22.285-1.848.385-2.677.72-2.677.72s.688-1.079 2-1.543c14.953-5.255 26.451 15.503-4.823 23.725 0-.002.359-.327.468-.617z"></path><path fill="#EA2D2E" d="M76.491 1.587S89.459 14.563 64.188 34.51c-20.266 16.006-4.621 25.13-.007 35.559-11.831-10.673-20.509-20.07-14.688-28.815C58.041 28.42 81.722 22.195 76.491 1.587z"></path><path fill="#0074BD" d="M52.214 126.021c22.476 1.437 57-.8 57.817-11.436 0 0-1.571 4.032-18.577 7.231-19.186 3.612-42.854 3.191-56.887.874 0 .001 2.875 2.381 17.647 3.331z"></path></svg>""",
                """<svg viewBox="0 0 128 128"><path fill="#fff" d="M21.012 91.125c-5.538.003-10.038-4.503-10.039-10.04l-.002-30.739c-.002-5.532 4.497-10.037 10.028-10.038 2.689-.002 5.207 1.041 7.105 2.937s2.942 4.418 2.944 7.099l-.003 30.74a9.924 9.924 0 01-2.931 7.094 9.962 9.962 0 01-7.102 2.947m-.008-48.12c-4.053-.002-7.338 3.291-7.339 7.341l.005 30.736a7.347 7.347 0 007.341 7.348 7.338 7.338 0 007.339-7.347V50.342a7.345 7.345 0 00-7.346-7.337"></path><path fill="#fff" d="M99.742 44.527l-2.698-.001-66.119.009-2.699.001-.002-2.699c-.006-11.08 6.03-21.385 15.917-27.473l-3.844-7.017c-.47-.822-.588-1.863-.314-2.815a3.732 3.732 0 011.814-2.239 3.605 3.605 0 011.759-.447c1.362 0 2.609.739 3.267 1.933l4.023 7.329a37.842 37.842 0 0113.099-2.305c4.606-.002 9.023.777 13.204 2.311l4.017-7.341a3.711 3.711 0 013.263-1.932 3.712 3.712 0 011.761.438A3.706 3.706 0 0188 4.524a3.69 3.69 0 01-.318 2.832l-3.842 7.013c9.871 6.101 15.9 16.398 15.899 27.459l.003 2.699zM80.196 15.403l5.123-9.355a1.019 1.019 0 10-1.783-.981l-5.176 9.45c-4.354-1.934-9.229-3.021-14.382-3.016-5.142-.005-10.008 1.078-14.349 3.005l-5.181-9.429a1.009 1.009 0 00-1.379-.405c-.497.266-.68.891-.403 1.379l5.125 9.348c-10.07 5.194-16.874 15.084-16.868 26.439l66.118-.008c.003-11.351-6.789-21.221-16.845-26.427M48.94 29.86a2.772 2.772 0 01.003-5.545 2.78 2.78 0 012.775 2.774 2.775 2.775 0 01-2.778 2.771m30.107-.006a2.767 2.767 0 01-2.772-2.771 2.788 2.788 0 012.773-2.778 2.79 2.79 0 012.767 2.779 2.769 2.769 0 01-2.768 2.77m-27.336 96.305c-5.533-.001-10.036-4.501-10.037-10.038l-.002-13.567-2.638.003a10.453 10.453 0 01-7.448-3.082 10.437 10.437 0 01-3.083-7.452l-.01-47.627v-2.701h2.699l65.623-.01 2.7-.002v2.699l.007 47.633c.001 5.809-4.725 10.536-10.532 10.535l-2.654.002.003 13.562c0 5.534-4.502 10.039-10.033 10.039a9.933 9.933 0 01-7.098-2.937 9.952 9.952 0 01-2.947-7.096v-13.568H61.75v13.565c-.002 5.535-4.503 10.043-10.039 10.042"></path><path fill="#fff" d="M31.205 92.022a7.82 7.82 0 007.831 7.837h5.333l.006 16.264c-.001 4.05 3.289 7.341 7.335 7.342a7.342 7.342 0 007.338-7.348l.001-16.259 9.909-.003-.001 16.263c.004 4.051 3.298 7.346 7.343 7.338 4.056.003 7.344-3.292 7.343-7.344l-.005-16.259 5.353-.001c4.319.001 7.832-3.508 7.832-7.837l-.009-47.635-65.621.012.012 47.63zm75.791-.91c-5.536.001-10.039-4.498-10.038-10.036l-.008-30.738c.002-5.537 4.498-10.041 10.031-10.041 5.54-.001 10.046 4.502 10.045 10.038l.003 30.736c.001 5.534-4.498 10.042-10.033 10.041m-.01-48.116c-4.053-.004-7.337 3.287-7.337 7.342l.003 30.737a7.336 7.336 0 007.342 7.34 7.338 7.338 0 007.338-7.343l-.008-30.736a7.335 7.335 0 00-7.338-7.34"></path><path fill="#A4C439" d="M21.004 43.005c-4.053-.002-7.338 3.291-7.339 7.341l.005 30.736a7.338 7.338 0 007.342 7.343 7.33 7.33 0 007.338-7.342V50.342a7.345 7.345 0 00-7.346-7.337m59.192-27.602l5.123-9.355a1.023 1.023 0 00-.401-1.388 1.022 1.022 0 00-1.382.407l-5.175 9.453c-4.354-1.938-9.227-3.024-14.383-3.019-5.142-.005-10.013 1.078-14.349 3.005l-5.181-9.429a1.01 1.01 0 00-1.378-.406 1.007 1.007 0 00-.404 1.38l5.125 9.349c-10.07 5.193-16.874 15.083-16.868 26.438l66.118-.008c.003-11.351-6.789-21.221-16.845-26.427M48.94 29.86a2.772 2.772 0 01.003-5.545 2.78 2.78 0 012.775 2.774 2.775 2.775 0 01-2.778 2.771m30.107-.006a2.77 2.77 0 01-2.772-2.771 2.793 2.793 0 012.773-2.778 2.79 2.79 0 012.767 2.779 2.767 2.767 0 01-2.768 2.77M31.193 44.392l.011 47.635a7.822 7.822 0 007.832 7.831l5.333.002.006 16.264c-.001 4.05 3.291 7.342 7.335 7.342 4.056 0 7.342-3.295 7.343-7.347l-.004-16.26 9.909-.003.004 16.263c0 4.047 3.293 7.346 7.338 7.338 4.056.003 7.344-3.292 7.343-7.344l-.005-16.259 5.352-.004a7.835 7.835 0 007.836-7.834l-.009-47.635-65.624.011zm83.134 5.943a7.338 7.338 0 00-7.341-7.339c-4.053-.004-7.337 3.287-7.337 7.342l.006 30.738a7.334 7.334 0 007.339 7.339 7.337 7.337 0 007.338-7.343l-.005-30.737z"></path></svg>"""
            ]
        }
    ]
    
    logfire.debug("Returning skills.")
    return skills[:limit] if limit > 0 else skills

# Send an email to the web3forms API
@logfire.instrument("Sending email")
def sendEmail(name: str, email: str, body: str) -> bool:
    try:
        url = "https://api.web3forms.com/submit"
        requestBody = {
            "access_key": WEB3FORMS_KEY,
            "email": email,
            "subject": f"Portfolio contact attempt by {name}",
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
            logfire.error(f"Error sending email. Response code: {response.status_code}", response=response)
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
