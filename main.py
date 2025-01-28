from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

# Get the Github account details
def getGithubAccount():
    url = "https://api.github.com/users/CommanderKV"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "name": data["name"],
            "userName": data["login"],
            "avatar": data["avatar_url"],
            "followers": data["followers"],
            "following": data["following"],
            "repos": data["public_repos"],
            "url": data["html_url"]
        }
    else:
        return {
            "name": "Kyler Visser",
            "login": "CommanderKV",
            "avatar": "https://avatars.githubusercontent.com/u/62476048?v=4",
            "followers": 0,
            "following": 0,
            "repos": 0,
            "url": "https://www.github.com/CommanderKV"
        }


def getGithubRepos(limit: int=-1):
    url = "https://api.github.com/users/CommanderKV/repos"
    response = requests.get(url)
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
            "url": repo["html_url"]
            }
            for repo in repos
        ]
    else:
        return []

# GET: /
@app.route("/")
def home():
    projects = getGithubRepos(3)
    return render_template(
        "home.html", 
        projects=projects, 
        account=getGithubAccount()
    )

# GET: /api
@app.route("/api", methods=["GET"])
def api():
    return jsonify({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run(debug=True)
