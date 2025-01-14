import asyncio

import time
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
from utils import parse_dext_bot_message, parse_ttf_bot_message, generate_report
import os
import backoff

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL')

DEXT_BOT_USERNAME = "DEXTNewPairsBotBSC"
TTF_BOT_USERNAME = "ttfbotbot"
HONEYPOT_API_URL = "https://api.honeypot.is/v2/IsHoneypot"


app = Client("tg_bot", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER)
response_event = asyncio.Event()
ttf_bot_response: str | None = None


@backoff.on_exception(backoff.expo, exception=KeyError, max_tries=3, max_time=5)
async def call_honeypot(token_address: str) -> dict:
    print("Calling honeypot.is API")
    response = requests.get(HONEYPOT_API_URL, params={"address": token_address})

    honeypot_data = response.json()
    return {"risk": honeypot_data['summary']["risk"], "riskLevel": honeypot_data['summary']["riskLevel"]}


async def call_ttfbot(token_address: str):
    print("Calling TTF Bot")
    return await app.send_message(TTF_BOT_USERNAME, text=token_address)


async def wait_for_ttf_bot_response():
    global response_event
    await response_event.wait()
    response_event.clear()


@app.on_message(filters.chat(TTF_BOT_USERNAME))
async def ttfbot_response_handler(client, message):
    global response_event, ttf_bot_response
    ttf_bot_response = message.text
    response_event.set()


async def get_new_contract(message: Message):
    print(f"Received new message from DEXT Bot")
    token_data = parse_dext_bot_message(message=message.text)
    token_data["timestamp"] = message.date.isoformat()
    token_address = token_data.get("token_address")

    # skip messages without token address
    if token_address:
        send_message_to_ttf_bot_task = call_ttfbot(token_address)
        send_message_to_honeypot_api_task = call_honeypot(token_address)

        _, honeypot_data = await asyncio.gather(send_message_to_ttf_bot_task, send_message_to_honeypot_api_task)

        await wait_for_ttf_bot_response()

        ttf_data = parse_ttf_bot_message(ttf_bot_response)
        token_data.update(ttf_data)
        token_data.update(honeypot_data)
        return token_data


@app.on_message(filters.chat(DEXT_BOT_USERNAME))
async def new_message_handler(client: Client, message: Message):
    start_time = time.perf_counter()

    token_data = await get_new_contract(message)
    report = generate_report(token_data)
    await client.send_message(TARGET_CHANNEL, report)

    end_time = time.perf_counter()
    print(f"Delay: {end_time - start_time}")


if __name__ == "__main__":
    print("Starting bot...")
    app.run()
