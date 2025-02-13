from flask import *
import logfire

app = Blueprint("dashboard", __name__)

@app.route("/dashboard")
def home():
    with logfire.span("GET /dashboard"):
        logfire.info("Rendering dashboard")
        return render_template_string("<h1>Dashboard</h1>")