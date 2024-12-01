import os
from pymongo import MongoClient
from dotenv import load_dotenv
from notifications import send_line_summary
from pytz import timezone
from datetime import datetime, timedelta
from config import EMOTIONS_COLLECTION, WATER_COLLECTION, USERS_COLLECTION
from sensor_data_sync import fetch_sensor_data

load_dotenv()
tz = timezone("Asia/Bangkok")

def store_user_id(user_id):
    """
    Store user ID in the database if it doesn't exist
    
    :param user_id: LINE user ID to store
    """
    if USERS_COLLECTION.find_one({"user_id": user_id}) is None:
        USERS_COLLECTION.insert_one({"user_id": user_id})
        print(f"User ID {user_id} has been added to the database.")
    else:
        print(f"User ID {user_id} already exists in the database.")

def count_water_times_today():
    """
    Count water times for today
    
    :return: Tuple of (date, water times count) or None
    """
    today_date = datetime.now().strftime("%Y-%m-%d")
    record = WATER_COLLECTION.find_one({"date": today_date})
    if not record or "water_time" not in record:
        return None

    water_times_count = len(record["water_time"])
    return today_date, water_times_count

def get_latest_sensor_averages():
    """
    Retrieve the latest sensor averages from MongoDB
    
    :return: Tuple of (temperature, humidity)
    """
    try:
        MONGODB_URI = os.getenv("MONGODB_URI")
        mongo_client = MongoClient(MONGODB_URI)
        
        try:
            db = mongo_client["emotion_detection"]
            sensor_averages_collection = db["sensor_averages"]
            
            # Get today's date
            today = datetime.now(tz).strftime("%Y-%m-%d")
            
            # Fetch today's sensor data
            sensor_data = sensor_averages_collection.find_one({"date": today})
            
            if sensor_data and 'averages' in sensor_data:
                temperature = sensor_data['averages'].get('temperature', 22.0)
                humidity = sensor_data['averages'].get('humidity', 60.0)
                return temperature, humidity
            
            return 22.0, 60.0  # Default values if no data found
        
        except Exception as e:
            print(f"Error fetching sensor averages: {e}")
            return 22.0, 60.0
        
        finally:
            mongo_client.close()
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return 22.0, 60.0

def summarize_emotion_and_water(auto_send=True):
    """
    Generate a comprehensive daily summary of plant care, emotions, and watering
    
    :param auto_send: If True, sends summary to all registered users via LINE
    :return: Summary string
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    today = datetime.now(tz).isoformat()
    todayYMD = today[0:10]
    tmr = datetime.now(tz) + timedelta(days=1)
    tmrYMD = tmr.isoformat()[0:10]
    total_emotions = EMOTIONS_COLLECTION.count_documents({
        "date_time": {
            "$gte": todayYMD + "T00:00:00+07:00",
            "$lt": tmrYMD + "T00:00:00+07:00"
        }
    })
    
    print(total_emotions)
    print(datetime.strptime(current_date, "%Y-%m-%d"))
    
    emotion_counts = {}
    if total_emotions > 0:
        emotion_pipeline = [
            {
                "$match": {
                    "date_time": {
                        "$gte": todayYMD + "T00:00:00+07:00", 
                        "$lt": tmrYMD + "T00:00:00+07:00"
                    }
                }
            },
            {
                "$group": {
                    "_id": "$emotion",
                    "count": {"$sum": 1}
                }
            }
        ]
        emotion_results = list(EMOTIONS_COLLECTION.aggregate(emotion_pipeline))
        
        emotion_counts = {
            result['_id']: {
                'count': result['count'],
                'percentage': round((result['count'] / total_emotions) * 100, 1)
            } for result in emotion_results
        }
    
    water_data = WATER_COLLECTION.find_one({"date": current_date})
    water_count = len(water_data["water_time"]) if water_data and "water_time" in water_data else 0
    
    # Fetch latest temperature and humidity
    temperature, humidity = get_latest_sensor_averages()
    
    summary = f"🌱 Plant Care Update for Today: 🌱\n\n" \
            f"🌿 Watering: You've watered the plant {water_count} times today.\n" \
            f"🌡️ Temperature: Current temperature is {round(temperature)}°C.\n" \
            f"💨 Humidity: Current humidity is {round(humidity)}%.\n\n" \
            f"Emotion Analysis for Today:\n" \
            f"😀 Happy: {emotion_counts.get('happy', {'percentage': 0})['percentage']}%\n" \
            f"😠 Angry: {emotion_counts.get('angry', {'percentage': 0})['percentage']}%\n" \
            f"😢 Sad: {emotion_counts.get('sad', {'percentage': 0})['percentage']}%\n" \
            f"🙂 Neutral: {emotion_counts.get('neutral', {'percentage': 0})['percentage']}%\n" \
            f"😨 Fear: {emotion_counts.get('fear', {'percentage': 0})['percentage']}%\n" \
            f"🤢 Disgust: {emotion_counts.get('disgust', {'percentage': 0})['percentage']}%\n" \
            f"😲 Surprise: {emotion_counts.get('surprise', {'percentage': 0})['percentage']}%\n\n" \
            f"Keep it up! 🌱"

    
    print(summary)
    
    # Send summary to all users only if auto_send is True
    if auto_send:
        send_line_summary(summary)
    
    return summary

def check_sensor_conditions():
    """
    Check real-time sensor conditions and send notifications if thresholds are exceeded
    """
    sensor_data, sensor_id = fetch_sensor_data()  # Fetch real-time data
    if not sensor_data:
        print("No real-time sensor data found.")
        return

    notifications = []

    # Temperature check
    temperature = sensor_data.get('temperature', 0)
    if temperature < 20:
        notifications.append(f"⚠️ Too cold! Current temperature is {temperature}°C 🥶")
    elif temperature > 35:
        notifications.append(f"⚠️ Too hot! Current temperature is {temperature}°C 🥵")

    # Light intensity check
    light_intensity = sensor_data.get('lightIntensity_val', 0)
    if light_intensity < 300:
        notifications.append(f"⚠️ Low light in the room! Current brightness level is {light_intensity} lux 💡")

    # Air quality check
    air_quality = sensor_data.get('airQuality_val', 0)
    if air_quality > 1536:
        notifications.append(f"⚠️ Poor air quality detected! Current air quality index is {air_quality} 😷")

    # Send notifications if any
    if notifications:
        notification_message = "🌿 **Real-Time Environment Alerts:**\n" + "\n".join(notifications)
        send_line_summary(notification_message)
        print("Sent real-time environment notifications:", notification_message)
    else:
        print("No critical real-time sensor conditions detected. 🌟")
