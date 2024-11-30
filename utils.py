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

def summarize_emotion_and_water():
    """
    Summarize daily emotions and water tracking
    Sends summary via LINE to all registered users
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Count happy emotions for today
    count_happy_emotion = EMOTIONS_COLLECTION.count_documents({
        "emotion": "happy",
        "date_time": {
            "$gte": datetime.strptime(current_date, "%Y-%m-%d"), 
            "$lt": datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)
        }
    })
    
    # Get water data for today
    water_data = WATER_COLLECTION.find_one({"date": current_date})
    
    # Default water count to 0 if no data
    water_count = len(water_data["water_time"]) if water_data and "water_time" in water_data else 0
    
    # Create summary message
    summary_message = f"วันนี้ ({current_date})\nจำนวนครั้งที่มีอารมณ์ดี: {count_happy_emotion}\nจำนวนครั้งที่รดน้ำ: {water_count}"
    
    # Print local log
    print(summary_message)
    
    # Send LINE notification
    send_line_summary(summary_message)