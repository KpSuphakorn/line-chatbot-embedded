from datetime import datetime, timedelta
from config import EMOTIONS_COLLECTION, WATER_COLLECTION, USERS_COLLECTION
from notifications import send_line_summary

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

def summarize_emotion_and_water(auto_send=True):
    """
    Generate a comprehensive daily summary of plant care, emotions, and watering
    
    :param auto_send: If True, sends summary to all registered users via LINE
    :return: Summary string
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    total_emotions = EMOTIONS_COLLECTION.count_documents({
        "date_time": {
            "$gte": datetime.strptime(current_date, "%Y-%m-%d"), 
            "$lt": datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)
        }
    })
    
    emotion_counts = {}
    if total_emotions > 0:
        emotion_pipeline = [
            {
                "$match": {
                    "date_time": {
                        "$gte": datetime.strptime(current_date, "%Y-%m-%d"), 
                        "$lt": datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)
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
    
    temperature = 22.0
    humidity = 60.0
    
    summary = f"🌱 Plant Care Update for Today: 🌱\n\n" \
              f"🌿 Watering: You've watered the plant {water_count} times today.\n" \
              f"🌡️ Temperature: Current temperature is {temperature}°C.\n" \
              f"💨 Humidity: Current humidity is {humidity}%.\n\n" \
              f"Emotion Analysis for Today:\n" \
              f"😀 Happy: {emotion_counts.get('happy', {'percentage': 0})['percentage']}%\n" \
              f"😠 Angry: {emotion_counts.get('angry', {'percentage': 0})['percentage']}%\n" \
              f"😢 Sad: {emotion_counts.get('sad', {'percentage': 0})['percentage']}%\n" \
              f"🙂 Neutral: {emotion_counts.get('neutral', {'percentage': 0})['percentage']}%\n\n" \
              f"Keep it up! 🌱"
    
    print(summary)
    
    # Send summary to all users only if auto_send is True
    if auto_send:
        send_line_summary(summary)
    
    return summary