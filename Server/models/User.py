from .. import db
import uuid

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column("id", db.Integer, primary_key=True)
    uid = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    userName = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    githubOAuthToken = db.Column(db.String(100), unique=True, nullable=False)
    
    roleId = db.Column(db.Integer, db.ForeignKey("roles.id"), default=2)
    role = db.relationship("Roles", back_populates="users")
    
    def __init__(self, githubOAuthToken: str, userName: str=None, name: str=None, email: str=None):
        self.githubOAuthToken = githubOAuthToken
        self.userName = userName
        self.name = name
        self.email = email
        self.roleId = 2
        self.uid = str(uuid.uuid4())

    def updateToken(self, token: str):
        self.githubOAuthToken = token
