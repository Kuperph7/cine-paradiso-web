import os

from dotenv import load_dotenv


load_dotenv()



DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

