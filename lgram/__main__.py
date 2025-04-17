import re
import asyncio
import importlib
import logging
from pathlib import Path
from pyrogram import Client, idle, filters
from pyrogram.types import Message
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
from pymongo import MongoClient
from lgram import LOGGER, app
from strings import string 
from lgram.functions import ALL_MODULES
from config import api_id, api_hash, MONGO_URI, MONGO_DB_NAME

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["cloned"]
mongo_collection = mongo_db[MONGO_DB_NAME]

async def init():
    await app.start()
    plugins_path = Path("lgram/functions")
    for module_path in plugins_path.glob("*.py"):
        module_name = module_path.stem
        importlib.import_module(f"lgram.functions.{module_name}")
    LOGGER("lgram modules").info("Successfully imported all modules.")
    await restart_clones()

    await idle()
    await app.stop()

async def restart_clones():
    LOGGER("Clone Manager").info("Restarting all cloned bots...")
    bots = list(mongo_db.bots.find())

    for bot in bots:
        bot_token = bot['token']
        try:
            ai = Client(
                f"{bot['username']}", api_id, api_hash,
                bot_token=bot_token,
                plugins={"root": "lgram.functionsclone"}
            )
            await ai.start()
            LOGGER("Clone Manager").info(f"Started cloned bot @{bot['username']}")
        except Exception as e:
            if "401 SESSION_REVOKED" in str(e):
                mongo_db.bots.delete_one({"token": bot_token})
                LOGGER("Clone Manager").warning(f"Deleted @{bot['username']} - Session revoked.")
            else:
                LOGGER("Clone Manager").exception(f"Error starting @{bot['username']}: {e}")


@app.on_message(filters.command("clone") & filters.private)
async def clone(client, message):
    await message.reply_text(string.cloneHelp_text)

@app.on_message((filters.regex(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}')) & filters.private)
async def on_clone(client, message):  
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        bot_token_matches = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', message.text, re.IGNORECASE)
        bot_token = bot_token_matches[0] if bot_token_matches else None

        if not bot_token:
            return await message.reply_text("No valid bot token found in the message.")

        bots = list(mongo_db.bots.find())
        existing_tokens = [bot['token'] for bot in bots]

        forward_from_id = message.forward_from.id if message.forward_from else None

        if bot_token in existing_tokens and forward_from_id == 93372553:
            return await message.reply_text("This bot is already cloned.")

        if forward_from_id != 93372553:
            return await message.reply_text("Please forward the token from BotFather.")

        msg = await message.reply_text("Cloning in progress, please wait...")

        try:
            ai = Client(
                f"{bot_token}", api_id, api_hash,
                bot_token=bot_token,
                plugins={"root": "lgram.functionsclone"},
            )
            await ai.start()
            bot = await ai.get_me()

            details = {
                'bot_id': bot.id,
                'is_bot': True,
                'user_id': user_id,
                'owner_id': user_id,
                'start_message': f"Hello! I'm your new bot @{bot.username}, cloned using lgram use /help to configure owner only",
                'user_name': user_name,
                'name': bot.first_name,
                'token': bot_token,
                'username': bot.username
            }

            mongo_db.bots.insert_one(details)
            await msg.edit_text(f"✅ Successfully cloned @{bot.username}. Now use your bot.")
        except BaseException as e:
            logging.exception("Error while cloning bot.")
            await msg.edit_text(f"<b>Bot Error:</b>\n\n<code>{e}</code>")
    except Exception as e:
        logging.exception("Error while handling message.")
        await message.reply_text("Something went wrong while processing the token.")

@app.on_message(filters.command("deleteclone") & filters.private)
async def delete_cloned_bot(client, message):
    try:
        bot_token_match = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', message.text)
        bot_token = bot_token_match[0] if bot_token_match else None

        if not bot_token:
            return await message.reply_text("Please provide a valid bot token to delete.")
        mongo_collection = mongo_db.bots
        cloned_bot = mongo_collection.find_one({"token": bot_token})

        if cloned_bot:
            mongo_collection.delete_one({"token": bot_token})
            await message.reply_text(f"Bot @{cloned_bot['username']} has been deleted.")
        else:
            await message.reply_text("bot not found")
    except Exception as e:
        logging.exception("Error while deleting cloned bot.")
        await message.reply_text("⚠️ An error occurred while deleting the cloned bot.")
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
