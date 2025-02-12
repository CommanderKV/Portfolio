import logfire
import dotenv
import sys
import os

# Check for the --env flag
try:
    pos = sys.argv.index("--env")
except ValueError:
    pos = -1
    
# Get the environment variables
if pos == -1 or len(sys.argv) <= pos + 1:
    if os.path.exists("/var/www/portfolioSite.env"):
        dotenv.load_dotenv("/var/www/portfolioSite.env")
    elif os.path.exists(os.path.join(os.getcwd(), "portfolioSite.env")):
        dotenv.load_dotenv("./portfolioSite.env")
    else:
        print("Missing required .env file.")
        sys.exit(1)
else:
    dotenv.load_dotenv(sys.argv[pos + 1])

# Setup logfire
logfire.configure(token=os.getenv("LOGFIRE_KEY"))

# ---------------------------------------
#     Import Server after configuring 
#   Logfire otherwise it will error out
# ---------------------------------------
from Server import create_app, db
app = create_app()

# Create tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)