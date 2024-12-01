from linebot.v3.messaging import TextMessage, Emoji
from utils import count_water_times_today, summarize_emotion_and_water, get_latest_sensor_averages
from pymongo import MongoClient
from datetime import datetime, timedelta
from pytz import timezone
import os
from dotenv import load_dotenv

load_dotenv()
tz = timezone("Asia/Bangkok")

def get_today_predominant_emotion():
    """
    Retrieve the predominant emotion for today based on count statistics.
    
    :return: Emotion string or None
    """
    today = datetime.now(tz).isoformat()
    todayYMD = today[0:10]
    tmr = datetime.now(tz) + timedelta(days=1)
    tmrYMD = tmr.isoformat()[0:10]
    
    try:
        MONGODB_URI = os.getenv("MONGODB_URI")
        mongo_client = MongoClient(MONGODB_URI)
        
        try:
            db = mongo_client["emotion_detection"]
            emotions_collection = db["emotions"]
            
            # Aggregate emotion counts for today
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
                },
                {
                    "$sort": {"count": -1}
                }
            ]
            emotion_results = list(emotions_collection.aggregate(emotion_pipeline))
            
            if emotion_results:
                return emotion_results[0]['_id']  # Return the emotion with the highest count
            
            return None  # No emotions recorded today
        
        except Exception as e:
            print(f"Error fetching predominant emotion: {e}")
            return None
        
        finally:
            mongo_client.close()
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def reponse_message(event):
    """
    Generate response messages for different user inputs
    
    :param event: LINE messaging event
    :return: TextMessage or None
    """
    request_message = event.message.text

    if request_message.startswith("Summary"):
        summary = summarize_emotion_and_water(auto_send=False)
        return TextMessage(text=summary)

    if request_message.startswith("Watering"):
        result = count_water_times_today()
        if result:
            today_date, water_count = result
            text_response = f"Good job! 🌱 You have watered your plant {water_count} times today. Keep up the great work in taking care of your green friend!"
        else:
            text_response = "I'm thirsty! 🌿 Water me before it's too late!"
        return TextMessage(text=text_response)
    
    if request_message.startswith("Emotions"):
        emotion = get_today_predominant_emotion()
        
        if not emotion:
            return TextMessage(text="No emotion data available today. Let's keep things positive! 🌱")
        
        emotion_responses = {
            "neutral": "You're feeling neutral today. 🙂 A peaceful vibe for you and your plant!",
            "calm": "You're feeling calm today. 🌼 A peaceful vibe for you and your plant!",
            "sad": "It seems like today’s a bit tough. 😔 You're feeling sad, but don’t worry, your plant’s here for you too!",
            "fear": "Feeling a bit scared today? 😟 You’re experiencing fear, but remember, everything will be okay. Your plant is here to calm your space!",
            "angry": "It looks like you're feeling angry today. 😠 Try to take a deep breath, and let’s give your plant some love—it might help!",
            "happy": "How's your day going? 😊 Today, you're feeling happy! Keep that positive energy flowing for a happy, healthy plant!",
            "surprise": "Wow! You're feeling surprised today. 😲 Let that exciting energy brighten your day and your plant’s too!",
            "disgust": "It seems you’re feeling disgusted today. 🤢 Remember, it’s okay to step back, breathe, and refresh your mind. Your plant’s here to help!"
        }
        
        # Default fallback response if emotion is not in the dictionary
        response_text = emotion_responses.get(
            emotion.lower(), 
            f"How's your day going? 😊 Today, you're feeling {emotion}! Keep that positive energy flowing for a happy, healthy plant!"
        )
        
        return TextMessage(text=response_text)

    if request_message.startswith("Environment"):
        # ดึงข้อมูลอุณหภูมิและความชื้น
        temperature, humidity = get_latest_sensor_averages()
        
        # เพิ่มข้อความตอบกลับ
        response_text = (
            f"Here's an update on your room's environment: 🌡️ Temperature: {round(temperature)}°C | 💧 Humidity: {round(humidity)}%. "
            "Stay comfortable, and let's keep the plant happy!"
        )
        return TextMessage(text=response_text)

    return None