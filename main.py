from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, jsonify, request
from getColors import run as getColors
import regex as re
import requests
import dotenv
import copy
import sys
import os

# Make the app
app = Flask(__name__)

# Get the environment variables
found = False
for pos, arg in enumerate(sys.argv):
    if arg == "--env":
        dotenv.load_dotenv(sys.argv[pos + 1])
        found = True

if not found:
    dotenv.load_dotenv("/var/www/portfolioSite.env")

COLORS = getColors()
try:
    GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
    WEB3FORMS_KEY = os.getenv("WEB3FORMS_KEY")
except Exception as e:
    print(f"Error loading environment variables {e}")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_API_KEY}"
}

# Get the Github account details
def getGithubAccount(repositories: list[dict]=[]) -> dict:
    # Duplicate the repositories
    repos = copy.deepcopy(repositories)
    
    # Get the account details
    url = "https://api.github.com/users/CommanderKV"
    response = requests.get(
        url,
        headers=HEADERS
    )
    if response.status_code == 200:
        # Get the language data
        languages = {}
        total = 0
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

def getGithubRepos(limit: int=-1) -> list[dict]:
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
                result[key] = {
                    "percent": round((data[key] / total) * 100, 1),
                    "color": COLORS[key]["color"] if key in COLORS else "#000000"
                }
            
            return result
        else:
            return {}
        
    
    url = "https://api.github.com/users/CommanderKV/repos"
    response = requests.get(
        url,
        headers=HEADERS
    )
    if response.status_code == 200:
        # Get the first 3 repos
        repos = response.json()
        repos = sorted(repos, key=lambda x: x["updated_at"], reverse=True)
        repos = repos[:limit] if limit > 0 else repos
        
        # Return the required data
        return [
            {
                "name": repo["name"],
                "description": repo["description"] or "No description available",
                "stars": repo["stargazers_count"],
                "forks": repo["forks"],
                "language": repo["language"] or "Unknown",
                "languages": getRepoLanguageMakeup(repo["languages_url"]),
                "url": repo["html_url"]
            }
            for repo in repos
        ]
    else:
        print("Error getting Github repos at https://api.github.com/users/CommanderKV/repos")
        print(response.json())
        return []

def getSkills(limit: int=-1) -> list[dict]:
    # Get the skills
    skills = [
        {
            "name": "Database management",
            "description": "I have used SQL and MYSQL for database management in many different applications.",
            "icons": [
                """<!-- Generator: Adobe Illustrator 26.0.1, SVG Export Plug-In . SVG Version: 6.00 Build 0)  --><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" viewBox="0 0 24 24" style="enable-background:new 0 0 24 24;" xml:space="preserve" width="512" height="512"><g><path style="fill-rule:evenodd;clip-rule:evenodd;" d="M5.457,4.257c-0.277,0-0.472,0.033-0.669,0.082v0.033H4.82   c0.132,0.261,0.36,0.441,0.522,0.67c0.131,0.261,0.246,0.521,0.376,0.783C5.734,5.808,5.75,5.791,5.75,5.791   c0.23-0.162,0.344-0.424,0.344-0.816C5.996,4.86,5.98,4.747,5.898,4.632C5.8,4.469,5.588,4.388,5.457,4.257L5.457,4.257z"/><path style="fill-rule:evenodd;clip-rule:evenodd;" d="M22.107,18.442c-1.307-0.033-2.318,0.098-3.167,0.457   c-0.245,0.098-0.636,0.098-0.67,0.408c0.131,0.13,0.147,0.342,0.262,0.523c0.196,0.326,0.537,0.766,0.848,0.996   c0.343,0.261,0.686,0.521,1.045,0.75c0.636,0.393,1.355,0.621,1.974,1.013c0.36,0.228,0.718,0.522,1.079,0.767   c0.179,0.13,0.292,0.343,0.521,0.424V23.73c-0.115-0.146-0.147-0.359-0.261-0.523c-0.163-0.162-0.327-0.31-0.49-0.472   c-0.474-0.637-1.062-1.191-1.697-1.648c-0.523-0.36-1.666-0.85-1.877-1.452c0,0-0.017-0.017-0.033-0.033   c0.359-0.033,0.784-0.164,1.127-0.263c0.554-0.146,1.06-0.113,1.631-0.26c0.262-0.066,0.523-0.148,0.785-0.228v-0.148   c-0.295-0.293-0.506-0.686-0.817-0.963c-0.832-0.718-1.747-1.419-2.693-2.008c-0.507-0.327-1.16-0.538-1.699-0.816   c-0.195-0.098-0.521-0.146-0.636-0.311c-0.294-0.359-0.458-0.832-0.67-1.257c-0.473-0.897-0.931-1.892-1.338-2.84   c-0.294-0.636-0.473-1.272-0.832-1.86c-1.682-2.775-3.51-4.456-6.317-6.105C7.579,2.2,6.861,2.053,6.094,1.874   C5.685,1.856,5.278,1.825,4.87,1.809C4.608,1.694,4.346,1.384,4.118,1.237c-0.931-0.587-3.329-1.86-4.015-0.179   c-0.441,1.062,0.653,2.106,1.029,2.645c0.277,0.375,0.637,0.8,0.832,1.224C2.078,5.204,2.11,5.498,2.225,5.791   c0.261,0.718,0.505,1.518,0.849,2.188C3.253,8.322,3.449,8.682,3.677,8.99c0.132,0.181,0.36,0.261,0.409,0.556   C3.858,9.872,3.84,10.362,3.71,10.77c-0.587,1.845-0.359,4.13,0.474,5.484c0.261,0.408,0.881,1.306,1.714,0.963   c0.734-0.293,0.571-1.224,0.783-2.039c0.049-0.197,0.016-0.327,0.114-0.457v0.033c0.228,0.456,0.457,0.896,0.67,1.355   c0.506,0.799,1.387,1.632,2.123,2.186c0.391,0.295,0.701,0.8,1.191,0.98v-0.049h-0.032c-0.098-0.146-0.245-0.212-0.375-0.326   c-0.294-0.294-0.62-0.653-0.849-0.98c-0.685-0.914-1.29-1.926-1.828-2.971c-0.262-0.507-0.49-1.062-0.702-1.567   c-0.098-0.195-0.098-0.49-0.261-0.587c-0.246,0.359-0.604,0.669-0.783,1.109c-0.31,0.703-0.343,1.568-0.458,2.466   c-0.065,0.017-0.032,0-0.065,0.032c-0.522-0.13-0.701-0.669-0.898-1.125c-0.489-1.16-0.572-3.021-0.147-4.36   c0.114-0.342,0.605-1.419,0.408-1.746C4.689,8.859,4.363,8.682,4.184,8.436c-0.212-0.31-0.442-0.701-0.587-1.045   c-0.392-0.914-0.589-1.926-1.012-2.84c-0.196-0.425-0.54-0.866-0.816-1.257C1.458,2.853,1.115,2.543,0.87,2.021   c-0.081-0.18-0.195-0.474-0.065-0.669c0.032-0.131,0.098-0.18,0.229-0.213C1.245,0.96,1.85,1.188,2.061,1.286   C2.666,1.53,3.172,1.76,3.677,2.102c0.229,0.164,0.474,0.474,0.767,0.556h0.343c0.522,0.113,1.11,0.032,1.6,0.179   c0.864,0.277,1.648,0.685,2.35,1.126c2.138,1.355,3.901,3.282,5.092,5.583c0.196,0.375,0.279,0.718,0.458,1.109   c0.343,0.802,0.768,1.618,1.11,2.4c0.343,0.767,0.67,1.55,1.16,2.188c0.244,0.342,1.224,0.522,1.665,0.702   c0.326,0.146,0.832,0.277,1.126,0.456c0.555,0.342,1.109,0.735,1.632,1.111C21.241,17.708,22.058,18.115,22.107,18.442   L22.107,18.442z"/></g></svg>"""
            ]
        },
        {
            "name": "Web Development",
            "description": "I have developed web apps using HTML, CSS, and JavaScript.",
            "icons": [
                """<!-- Generator: Adobe Illustrator 26.0.1, SVG Export Plug-In . SVG Version: 6.00 Build 0)  --><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" viewBox="0 0 24 24" style="enable-background:new 0 0 24 24;" xml:space="preserve" width="512" height="512"><g><path d="M5.081,0h1.078v1.069h0.994V0h1.078v3.234H7.153V2.156H6.169v1.078H5.081L5.081,0z M9.656,1.078H8.705V0h2.986v1.078   h-0.956v2.156H9.656V1.078z M12.164,0h1.13l0.694,1.139L14.681,0h1.13v3.234h-1.078V1.631l-0.755,1.162l-0.755-1.162v1.603h-1.059   V0z M16.345,0h1.078v2.166h1.528v1.069h-2.606V0z"/><path d="M3.497,4.716l1.547,17.362L11.986,24l6.97-1.931l1.547-17.353H3.497z M6.656,8.264h5.334v2.128h-3l0.197,2.18h2.803v2.123   H7.237L6.656,8.264z M12,14.7h2.616l-0.248,2.766L12,18.101V14.7z M17.625,20.953L12,22.523v-2.198l-4.369-1.219l-0.3-3.342h2.138   l0.15,1.702l2.377,0.636l-0.005,0.001v2.212L12,20.313l4.35-1.207l0.586-6.534H12v-2.18h5.128l0.197-2.128H12V6.141h6.952   L17.625,20.953z"/><polygon points="12,12.572 16.936,12.572 16.35,19.106 12,20.313 12,18.101 14.367,17.466 14.616,14.7 12,14.7  "/><polygon points="17.325,8.264 17.128,10.392 12,10.392 12,8.264  "/><path d="M11.991,8.264v2.128H12V8.264H11.991z M11.991,12.572v2.123H12v-2.123H11.991z M11.995,18.102l-0.005,0.001v2.212   L12,20.313v-2.21L11.995,18.102z"/><path d="M11.991,8.264v2.128h5.137l0.197-2.128H11.991z M11.991,12.572V14.7h2.625l-0.248,2.766L12,18.101l-0.005,0.001   l-0.005,0.001v2.212L12,20.313l4.35-1.207l0.586-6.534H11.991z"/></g></svg>""", 
                """<!-- Generator: Adobe Illustrator 26.0.1, SVG Export Plug-In . SVG Version: 6.00 Build 0)  --><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" viewBox="0 0 24 24" style="enable-background:new 0 0 24 24;" xml:space="preserve" width="512" height="512"><polygon points="6.972,14.935 7.274,18.316 11.994,19.59 11.998,19.589 11.998,19.589 16.725,18.313 17.217,12.816 2.528,12.816   2.149,8.578 17.584,8.578 17.97,4.238 1.771,4.238 1.385,0 22.615,0 20.686,21.59 12.013,23.994 12.013,23.995 11.993,24   3.312,21.59 2.718,14.935 "/></svg>""", 
                """<svg xmlns="http://www.w3.org/2000/svg" id="js" viewBox="0 0 24 24" width="512" height="512"><path d="M16.122,18.75a2.456,2.456,0,0,0,2.225,1.37c.934,0,1.531-.467,1.531-1.113,0-.773-.613-1.047-1.642-1.5l-.564-.242c-1.627-.693-2.708-1.562-2.708-3.4a3.014,3.014,0,0,1,3.3-2.979A3.332,3.332,0,0,1,21.474,12.7l-1.756,1.127a1.534,1.534,0,0,0-1.451-.966.982.982,0,0,0-1.08.966c0,.677.419.951,1.387,1.37l.564.241c1.916.822,3,1.66,3,3.543,0,2.031-1.595,3.143-3.737,3.143a4.333,4.333,0,0,1-4.11-2.306Zm-7.967.2c.354.628.677,1.16,1.451,1.16.741,0,1.209-.29,1.209-1.418V11.02H13.07v7.7a3.063,3.063,0,0,1-3.368,3.4,3.5,3.5,0,0,1-3.383-2.06Z"/></svg>""",
                """<!-- Generator: Adobe Illustrator 26.0.1, SVG Export Plug-In . SVG Version: 6.00 Build 0)  --><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" viewBox="0 0 24 24" style="enable-background:new 0 0 24 24;" xml:space="preserve" width="512" height="512"><g><path d="M1.899,8.507h3.559C6.503,8.516,7.26,8.817,7.73,9.41c0.469,0.593,0.624,1.403,0.465,2.43   c-0.062,0.469-0.199,0.93-0.412,1.381c-0.204,0.452-0.487,0.859-0.85,1.222c-0.443,0.46-0.916,0.753-1.421,0.877   c-0.505,0.124-1.027,0.186-1.567,0.186H2.351L1.846,18.03H0L1.899,8.507L1.899,8.507 M3.453,10.021l-0.797,3.984   c0.053,0.009,0.106,0.013,0.159,0.013c0.062,0,0.124,0,0.186,0c0.85,0.009,1.558-0.075,2.125-0.252   c0.567-0.186,0.947-0.832,1.142-1.939c0.159-0.93,0-1.465-0.478-1.607c-0.469-0.142-1.058-0.208-1.766-0.199   c-0.106,0.009-0.208,0.013-0.305,0.013c-0.088,0-0.181,0-0.279,0L3.453,10.021"/><path d="M10.297,5.97h1.833l-0.518,2.537h1.647c0.903,0.018,1.576,0.204,2.019,0.558c0.452,0.354,0.584,1.027,0.398,2.019   l-0.89,4.423h-1.859l0.85-4.223c0.088-0.443,0.062-0.757-0.08-0.943c-0.142-0.186-0.447-0.279-0.916-0.279l-1.474-0.013   l-1.089,5.458H8.385L10.297,5.97L10.297,5.97"/><path d="M17.644,8.507h3.559c1.045,0.009,1.802,0.31,2.271,0.903c0.469,0.593,0.624,1.403,0.465,2.43   c-0.062,0.469-0.199,0.93-0.412,1.381c-0.204,0.452-0.487,0.859-0.85,1.222c-0.443,0.46-0.916,0.753-1.421,0.877   c-0.505,0.124-1.027,0.186-1.567,0.186h-1.594l-0.505,2.523h-1.846L17.644,8.507L17.644,8.507 M19.198,10.021l-0.797,3.984   c0.053,0.009,0.106,0.013,0.159,0.013c0.062,0,0.124,0,0.186,0c0.85,0.009,1.558-0.075,2.125-0.252   c0.567-0.186,0.947-0.832,1.142-1.939c0.159-0.93,0-1.465-0.478-1.607c-0.469-0.142-1.058-0.208-1.766-0.199   c-0.106,0.009-0.208,0.013-0.305,0.013c-0.088,0-0.181,0-0.279,0L19.198,10.021"/></g></svg>"""
            ]
        },
        {
            "name": "Python Development",
            "description": "Python was my first language that I started developing in and I feel fairly confident in my abilities with it.",
            "icons": [
                """<!-- Generator: Adobe Illustrator 26.0.1, SVG Export Plug-In . SVG Version: 6.00 Build 0)  --><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Capa_1" x="0px" y="0px" viewBox="0 0 24 24" style="enable-background:new 0 0 24 24;" xml:space="preserve" width="512" height="512"><g><g id="g2303_00000031922597863478397790000004595394903733610625_"><path id="path1948_00000134962089881649523420000009399677824023126944_" d="M11.859,0C10.88,0.005,9.945,0.088,9.123,0.234    C6.7,0.662,6.26,1.558,6.26,3.21v2.182h5.726V6.12H6.26H4.111c-1.664,0-3.121,1-3.577,2.903c-0.526,2.181-0.549,3.542,0,5.819    c0.407,1.695,1.379,2.903,3.043,2.903h1.969v-2.616c0-1.89,1.635-3.557,3.577-3.557h5.719c1.592,0,2.863-1.311,2.863-2.91V3.21    c0-1.552-1.309-2.717-2.863-2.976C13.858,0.07,12.837-0.004,11.859,0z M8.762,1.755c0.591,0,1.074,0.491,1.074,1.094    c0,0.601-0.483,1.088-1.074,1.088c-0.594,0-1.074-0.486-1.074-1.088C7.688,2.246,8.169,1.755,8.762,1.755z"/><path id="path1950_00000083807539188134144630000011128538031068007323_" d="M18.418,6.12v2.543c0,1.971-1.671,3.63-3.577,3.63    H9.123c-1.567,0-2.863,1.341-2.863,2.91v5.452c0,1.552,1.349,2.464,2.863,2.91c1.812,0.533,3.55,0.629,5.719,0    c1.441-0.417,2.863-1.257,2.863-2.91v-2.182h-5.719v-0.727h5.719h2.863c1.664,0,2.284-1.161,2.863-2.903    c0.598-1.794,0.572-3.518,0-5.819c-0.411-1.657-1.197-2.903-2.863-2.903H18.418z M15.202,19.927c0.594,0,1.074,0.486,1.074,1.088    c0,0.604-0.481,1.094-1.074,1.094c-0.591,0-1.074-0.491-1.074-1.094C14.128,20.413,14.611,19.927,15.202,19.927z"/></g></g></svg>"""
            ]
        } 
    ]
    
    return skills[:limit] if limit > 0 else skills

# Send an email to the web3forms API
def sendEmail(name: str, email: str, body: str) -> bool:
    try:
        requestBody = {
            "access_key": WEB3FORMS_KEY,
            "email": email,
            "subject": f"Portfolio contact attempt by {name}",
            "message": body
        }
        response = requests.post(
            "https://api.web3forms.com/submit",
            json=requestBody
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"Error sending email {response.text}")
            return False
        
    except Exception as e:
        print(f"Error sending email {e}")
        return False

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

# -----------------------------
#   Update the github account 
#    and profile every hour 
# -----------------------------
def setRepos():
    global REPOS
    REPOS = getGithubRepos()
    print("Updated repos")

def setGithubAccount():
    global GITHUB_ACCOUNT
    GITHUB_ACCOUNT = getGithubAccount(REPOS)

scheduler = BackgroundScheduler()
scheduler.add_job(func=setRepos, trigger="interval", hours=1)
scheduler.add_job(func=setGithubAccount, trigger="interval", hours=1)
scheduler.start()

# GET: /
@app.route("/", methods=["GET"])
def home():
    return render_template(
        "home.html", 
        projects=REPOS[:3], 
        account=GITHUB_ACCOUNT,
        skills=getSkills(3),
        contact=CONTACT_INFO
    )

# GET: /projects
@app.route("/projects", methods=["GET"])
def projects():
    return render_template(
        "projects.html", 
        projects=REPOS,
        account=GITHUB_ACCOUNT,
        contact=CONTACT_INFO
    )

# GET: /contact
@app.route("/contact", methods=["GET"])
def contact():
    return render_template(
        "contact.html", 
        contact=CONTACT_INFO
    )

# GET: /skills
@app.route("/skills", methods=["GET"])
def skills():
    return render_template(
        "skills.html",
        skills=getSkills(),
        contact=CONTACT_INFO
    )
    
# GET: /login
@app.route("/login", methods=["GET"])
def login():
    return render_template(
        "login.html",
        contact=CONTACT_INFO
    )
# --------------
#   Api routes
# --------------
# GET: /api
@app.route("/api", methods=["GET"])
def api():
    return jsonify({"message": "Hello, World!"})

# POST: /contact
@app.route("/api/contact", methods=["POST"])
def apiContact():
    # Get data from the request
    data = request.json
    errors = {}
    
    # Validating name data
    if not data.get("name"):
        errors["name"] = "Name is required"
    elif len(data.get("name")) < 3:
        errors["name"] = "Must be at least 3 characters"
    
    # Validating email data
    if not data.get("email"):
        errors["email"] = "Email is required"
    elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", data.get("email")):
        errors["email"] = "Invalid email format"
    
    # Validating message data
    if not data.get("message"):
        errors["message"] = "Message is required"
    elif len(data.get("message")) < 10:
        errors["message"] = "Must be at least 10 characters"
        
    # If there are errors then return them with a status code of 400
    if errors:
        return jsonify({"success": False, "errors": errors}), 400
    
    # Send email
    if sendEmail(
        name=data.get("name"),
        email=data.get("email"),
        body=data.get("message")
    ):
        # Message was sent successfully
        return jsonify({"success": True, "message": "Message sent successfully!"})
    
    else:
        # Message failed to send
        return jsonify({"success": False, "message": "Failed to send message"}), 500

if __name__ == "__main__":
    app.run(debug=True)
