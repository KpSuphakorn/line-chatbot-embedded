from linebot.v3.messaging import TextMessage, Emoji
from utils import count_water_times_today, summarize_emotion_and_water

def reponse_message(event):
    """
    Generate response messages for different user inputs
    
    :param event: LINE messaging event
    :return: TextMessage or None
    """
    request_message = event.message.text
    
    if request_message.lower() == "hello":
        emoji_data = [
            {"index": 0, "productId": "5ac1bfd5040ab15980c9b435", "emojiId": "002"},
            {"index": 37, "productId": "5ac21c46040ab15980c9b442", "emojiId": "002"},
        ]
        emojis = [Emoji(**emoji) for emoji in emoji_data]

        text_response = "$ Hello/สวัสดีครับ from PythonDevBot $"
        return TextMessage(text=text_response, emojis=emojis)

    if request_message.startswith("พยากรณ์อากาศ"):
        return TextMessage(text="ขออภัย ตอนนี้ยังไม่มีข้อมูลพยากรณ์อากาศ")

    if request_message.startswith("รดน้ำ"):
        result = count_water_times_today()
        if result:
            today_date, water_count = result
            text_response = f"วันที่: {today_date}\nจำนวนครั้ง: {water_count}"
        else:
            text_response = "ไม่มีข้อมูลการรดน้ำสำหรับวันนี้"
        return TextMessage(text=text_response)

    if request_message.startswith("ดูภาพรวม"):
        # Generate summary without auto-sending
        summary = summarize_emotion_and_water(auto_send=False)
        return TextMessage(text=summary)

    return None