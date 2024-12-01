from linebot.v3.messaging import TextMessage, Emoji
from utils import count_water_times_today, summarize_emotion_and_water

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
        return TextMessage(text="ขออภัย ตอนนี้ยังไม่มีข้อมูลพยากรณ์อากาศ")

    if request_message.startswith("Environment"):
        return TextMessage(text="ขออภัย ตอนนี้ยังไม่มีข้อมูลพยากรณ์อากาศ")
    "Here's an update on your room's environment: 🌡️ Temperature: [temperature]°C | 💧 Humidity: [humidity]%. Stay comfortable, and let's keep the plant happy!"

    return None