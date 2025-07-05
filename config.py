import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Other configuration settings
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
API_ENDPOINT = os.getenv("API_ENDPOINT", "https://api.example.com/v1")

# Add more configuration variables as needed