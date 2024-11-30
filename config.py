import os
from dotenv import load_dotenv
from pymongo import MongoClient
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
try:
    mongo_client = MongoClient(MONGODB_URI)
    mongo_client.admin.command('ping')  # Test the connection
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error occurred while connecting to MongoDB: {e}")
    raise

# Database and Collections
DB = mongo_client["emotion_detection"]
EMOTIONS_COLLECTION = DB["emotions"]
WATER_COLLECTION = DB["water"]
USERS_COLLECTION = DB["users"]

# LINE Bot Configuration
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

line_configuration = Configuration(access_token=ACCESS_TOKEN)
line_bot_api = MessagingApi(ApiClient(line_configuration))