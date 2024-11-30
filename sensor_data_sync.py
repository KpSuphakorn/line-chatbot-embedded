import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

last_sensor_id = None

def fetch_sensor_data():
    """
    Fetch sensor data from Firebase API
    
    :return: Tuple of (sensor_data, sensor_id) or (None, None) if fetch fails
    """
    global last_sensor_id
    try:
        url = "https://embedded-project-1f031-default-rtdb.asia-southeast1.firebasedatabase.app/sensorData.json"
        
        response = requests.get(url)
        response.raise_for_status()
        
        sensor_data = response.json()
        
        sensor_data['timestamp'] = datetime.now()
        
        current_sensor_id = sensor_data.get('id')
        
        return sensor_data, current_sensor_id
    
    except requests.RequestException as e:
        print(f"Error fetching sensor data: {e}")
        return None, None

def store_sensor_data(sensor_data, current_sensor_id):
    """
    Store sensor data in MongoDB only if there's a change in sensor ID
    
    :param sensor_data: Dictionary of sensor data
    :param current_sensor_id: Unique identifier to detect changes
    """
    global last_sensor_id
    
    try:
        if (current_sensor_id is not None and 
            current_sensor_id != last_sensor_id):
            
            MONGODB_URI = os.getenv("MONGODB_URI")
            mongo_client = MongoClient(MONGODB_URI)
            
            try:
                db = mongo_client["emotion_detection"]
                sensor_collection = db["sensor_values"]
                
                result = sensor_collection.insert_one(sensor_data)
                print(f"New sensor data stored. Inserted ID: {result.inserted_id}")
                
                last_sensor_id = current_sensor_id
            
            except Exception as e:
                print(f"Error inserting sensor data: {e}")
            
            finally:
                mongo_client.close()
        else:
            print("No new sensor data to store.")
    
    except Exception as e:
        print(f"Error processing sensor data: {e}")

def main():
    """
    Main function to fetch and store sensor data
    """
    sensor_data, current_sensor_id = fetch_sensor_data()
    
    if sensor_data:
        store_sensor_data(sensor_data, current_sensor_id)

if __name__ == "__main__":
    main()