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
        # Initialize LINE messaging configuration
        configuration = Configuration(access_token=ACCESS_TOKEN)
        line_bot_api = MessagingApi(ApiClient(configuration))
        
        # Fetch all user IDs from the users collection
        users = USERS_COLLECTION.find()
        
        # Send message to each user
        for user in users:
            user_id = user.get('user_id')
            if user_id:
                try:
                    # Create a text message
                    text_message = TextMessage(text=message)
                    
                    # Push the message using the MessagingApi
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