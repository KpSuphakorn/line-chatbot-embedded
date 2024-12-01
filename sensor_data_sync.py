import requests
import os
from datetime import datetime, date
from dotenv import load_dotenv
from pymongo import MongoClient
import statistics

load_dotenv()

# Global variable to keep track of the last sensor ID
last_sensor_id = None

def fetch_sensor_data():
    """
    Fetch sensor data from Firebase API
    
    :return: Tuple of (sensor_data, sensor_id) or (None, None) if fetch fails
    """
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

def calculate_and_update_averages(current_data, current_sensor_id):
    """
    Calculate averages and update MongoDB
    
    :param current_data: Dictionary of current sensor data from Firebase
    :param current_sensor_id: Current sensor ID
    """
    global last_sensor_id
    
    try:
        MONGODB_URI = os.getenv("MONGODB_URI")
        mongo_client = MongoClient(MONGODB_URI)
        
        try:
            db = mongo_client["emotion_detection"]
            sensor_averages_collection = db["sensor_averages"]
            
            if (current_sensor_id is not None and 
                current_sensor_id != last_sensor_id):
                
                today = date.today().isoformat()
                
                today_record = sensor_averages_collection.find_one({
                    'date': today
                })
                
                update_data = {
                    'count': 1,
                    'timestamp': datetime.now(),
                    'date': today,
                    'id': current_sensor_id
                }
                
                sensor_keys = [
                    'temperature', 
                    'humidity', 
                    'airQuality_val', 
                    'lightIntensity_val', 
                    'soilMoisture'
                ]
                
                if today_record:
                    current_count = today_record.get('count', 1)
                    update_data['count'] = current_count + 1
                    
                    for key in sensor_keys:
                        if key in current_data and key in today_record:
                            new_average = (
                                (today_record[key] * current_count + current_data[key]) / 
                                (current_count + 1)
                            )
                            update_data[key] = round(new_average, 2)
                        else:
                            update_data[key] = current_data.get(key, 0)
                    
                    sensor_averages_collection.update_one(
                        {'date': today}, 
                        {'$set': update_data}
                    )
                    print(f"Updated daily sensor averages for {today}")
                else:
                    for key in sensor_keys:
                        update_data[key] = current_data.get(key, 0)
                    
                    sensor_averages_collection.insert_one(update_data)
                    print(f"Created new daily sensor averages for {today}")
                
                print("Updated/New Averages:", update_data)
                
                last_sensor_id = current_sensor_id
            else:
                print("No new sensor data to process.")
        
        except Exception as e:
            print(f"Error calculating and storing sensor averages: {e}")
        
        finally:
            mongo_client.close()
    
    except Exception as e:
        print(f"Error processing sensor data: {e}")

def fetch_and_store_sensor_data():
    """
    Main function to fetch sensor data and calculate averages
    """
    sensor_data, sensor_id = fetch_sensor_data()
    
    if sensor_data and sensor_id:
        calculate_and_update_averages(sensor_data, sensor_id)

def main():
    fetch_and_store_sensor_data()

if __name__ == "__main__":
    main()