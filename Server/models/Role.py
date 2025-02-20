from .. import db

class Roles(db.Model):
    __tablename__ = "roles"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    users = db.relationship("Users", back_populates="role")
    
    def __init__(self, name: str):
        self.name = name
