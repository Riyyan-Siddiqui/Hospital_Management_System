from dotenv import load_dotenv
import os

# Page configuration
PAGE_TITLE = "Hospital Management System"
PAGE_ICON = "🏥" 
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"


# Load environment variables from .env file

load_dotenv()

# MySQL Database configuration

load_dotenv()  # loads .env file in the root directory

DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME") or "hospital_db",
    'port': int(os.getenv("DB_PORT") or 3306)
}
