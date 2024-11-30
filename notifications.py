from linebot.v3.messaging import (
    TextMessage, 
    PushMessageRequest, 
    ApiClient, 
    MessagingApi, 
    Configuration
)
from config import USERS_COLLECTION, ACCESS_TOKEN, CHANNEL_SECRET

def send_line_summary(message):
    """
    Send summary message to all registered users
    
    :param message: Summary message to send
    """
    try:
        configuration = Configuration(access_token=ACCESS_TOKEN)
        line_bot_api = MessagingApi(ApiClient(configuration))
        
        users = USERS_COLLECTION.find()
        
        for user in users:
            user_id = user.get('user_id')
            if user_id:
                try:
                    text_message = TextMessage(text=message)
                    
                    line_bot_api.push_message(
                        push_message_request=PushMessageRequest(
                            to=user_id,
                            messages=[text_message]
                        )
                    )
                    print(f"Summary sent to user: {user_id}")
                except Exception as e:
                    print(f"Failed to send message to user {user_id}: {e}")
    except Exception as e:
        print(f"Error in sending LINE summary: {e}")