import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Header
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import (
    ApiClient, 
    MessagingApi, 
    Configuration, 
    ReplyMessageRequest, 
    TextMessage
)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config import ACCESS_TOKEN, CHANNEL_SECRET
from response_message import reponse_message
from utils import store_user_id, summarize_emotion_and_water
from sensor_data_sync import fetch_sensor_data, calculate_and_update_averages

app = FastAPI()

configuration = Configuration(access_token=ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=CHANNEL_SECRET)

@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    """
    Webhook callback for LINE messaging API
    """
    body = await request.body()
    body_str = body.decode('utf-8')
    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    """
    Handle incoming LINE messages
    """
    line_bot_api = MessagingApi(ApiClient(configuration))
    user_id = event.source.user_id 
    store_user_id(user_id)

    reply_message = reponse_message(event)

    if reply_message:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )

# Create scheduler for multiple tasks
scheduler = BackgroundScheduler()

# Existing summary job
summary_trigger = CronTrigger(hour=5, minute=00)
scheduler.add_job(summarize_emotion_and_water, summary_trigger)

# New sensor data fetch job - every 1 minute
sensor_trigger = IntervalTrigger(minutes=1)
def fetch_and_store_sensor_data():
    sensor_data, current_sensor_id = fetch_sensor_data()
    if sensor_data and current_sensor_id:
        calculate_and_update_averages(sensor_data, current_sensor_id)

scheduler.add_job(fetch_and_store_sensor_data, sensor_trigger)

scheduler.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")