from .. import db

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    userName = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    githubOAuthToken = db.Column(db.String(100), unique=True, nullable=False)
    
    def __init__(self, githubOAuthToken: str, userName: str=None, name: str=None, email: str=None):
        self.githubOAuthToken = githubOAuthToken
        self.userName = userName
        self.name = name
        self.email = email

