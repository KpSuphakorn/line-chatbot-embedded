import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def fetch_sensor_data():
    """
    Fetch sensor data from Firebase API
    
    :return: Dictionary of sensor data or None if fetch fails
    """
    try:
        url = "https://embedded-project-1f031-default-rtdb.asia-southeast1.firebasedatabase.app/sensorData.json"
        
        response = requests.get(url)
        response.raise_for_status()
        
        sensor_data = response.json()
        
        sensor_data['timestamp'] = datetime.now()
        
        return sensor_data
    
    except requests.RequestException as e:
        print(f"Error fetching sensor data: {e}")
        return None

def store_sensor_data(sensor_data):
    """
    Store sensor data in MongoDB
    
    :param sensor_data: Dictionary of sensor data
    """
    try:
        MONGODB_URI = os.getenv("MONGODB_URI")
        mongo_client = MongoClient(MONGODB_URI)
        
        db = mongo_client["emotion_detection"]
        sensor_collection = db["sensor_values"]
        
        if sensor_data:
            result = sensor_collection.insert_one(sensor_data)
            print(f"Sensor data stored successfully. Inserted ID: {result.inserted_id}")
        else:
            print("No sensor data to store.")
    
    except Exception as e:
        print(f"Error storing sensor data in MongoDB: {e}")
    finally:
        mongo_client.close()

def main():
    """
    Main function to fetch and store sensor data
    """
    sensor_data = fetch_sensor_data()
    
    store_sensor_data(sensor_data)

if __name__ == "__main__":
    main()