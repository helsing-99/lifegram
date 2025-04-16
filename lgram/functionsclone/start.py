from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["cloned"]
bots_collection = mongo_db["bots"]
users_collection = mongo_db["users"]

from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    try:
        me = await client.get_me()
        bot_data = bots_collection.find_one({"bot_id": me.id}) or bots_collection.find_one({"username": me.username})
        if bot_data:
           
            users_collection.update_one(
                {"user_id": message.from_user.id, "bot_id": me.id},
                {"$set": {"user_id": message.from_user.id, "bot_id": me.id}},
                upsert=True
            )

        if not bot_data:
            return await message.reply_text("This bot isn't registered in the database.")

        fsub_channels = bot_data.get("force_sub", [])
        not_joined = []
        buttons = []

        for chat_id in fsub_channels:
            try:
                member = await client.get_chat_member(chat_id, message.from_user.id)
                if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    raise UserNotParticipant  
            except:

                try:
                    chat = await client.get_chat(chat_id)
                    title = chat.title or "Join Channel"
                    if chat.username:
                        url = f"https://t.me/{chat.username}"
                    else:
                        invite_link = await client.export_chat_invite_link(chat.id)
                        url = invite_link
                    buttons.append([InlineKeyboardButton(title, url=url)])
                    not_joined.append(chat_id)
                except:
                    continue 

        if not_joined:
            buttons.append([InlineKeyboardButton("Verify membership", callback_data="check_fsub")])
            return await message.reply_text(
                "🚫 To use this bot, please join all the required channels:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        users_collection.update_one(
            {"user_id": message.from_user.id, "bot_id": me.id},
            {"$set": {"user_id": message.from_user.id, "bot_id": me.id}},
            upsert=True
        )

        custom_message = bot_data.get("start_message", "Hello! I'm alive.")
        await message.reply_text(custom_message)

    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")


@Client.on_message(filters.command("setstart") & filters.private)
async def set_start_message(client: Client, message: Message):
    me = await client.get_me()
    bot_data = bots_collection.find_one({"bot_id": me.id}) or bots_collection.find_one({"username": me.username})

    if not bot_data:
        return await message.reply_text("This bot is not registered in the database.")

    if message.from_user.id != bot_data.get("owner_id"):
        return await message.reply_text("You're not the owner of this bot.")

    try:
        new_msg = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("Please provide the new start message like:\n`/setstart Hello, I,m your bot.`")

    bots_collection.update_one(
        {"bot_id": me.id},
        {"$set": {"start_message": new_msg}}
    )

    await message.reply_text("Custom start message updated!")


@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_handler(client: Client, message: Message):
    me = await client.get_me()
    bot_data = bots_collection.find_one({"bot_id": me.id}) or bots_collection.find_one({"username": me.username})

    if not bot_data:
        return await message.reply_text("This bot is not registered in the database.")

    if message.from_user.id != bot_data.get("owner_id"):
        return await message.reply_text("You're not the owner of this bot.")

    try:
        broadcast_text = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("Please provide the message to broadcast like:\n`/broadcast Hello everyone!`")

    users = users_collection.find({"bot_id": me.id})
    total = 0
    success = 0
    failed = 0

    await message.reply_text("Broadcasting started...")

    for user in users:
        user_id = user["user_id"]
        total += 1
        try:
            await client.send_message(user_id, broadcast_text)
            success += 1
        except:
            failed += 1

    await message.reply_text(f"Broadcast finished.\n\nTotal: {total}\nSent: {success}\nFailed: {failed}")

@Client.on_message(filters.command("help") & filters.private)
async def help_handler(client: Client, message: Message):
    me = await client.get_me()
    bot_data = bots_collection.find_one({"bot_id": me.id}) or bots_collection.find_one({"username": me.username})

    if not bot_data:
        return await message.reply_text("This bot is not registered in the database.")

    if message.from_user.id != bot_data.get("owner_id"):
        return await message.reply_text("Only the bot owner can access the help menu.")

    help_text = (
    "<b>Owner Commands Guide</b>\n\n"
    "Use these commands to fully manage your cloned bot:\n\n"
    
    "<b>/setstart</b> <code>Your welcome message</code>\n"
    "Set or update the custom message users see when they press /start.\n\n"
    
    "<b>/broadcast</b> <code>Your message</code>\n"
    "Send a message to all users who have started your bot.\n\n"
    
    "<b>/addfsub</b> <code>channel_id or @username</code>\n"
    "Add a channel or group where users must be a member to use the bot.\n\n"
    
    "<b>/delfsub</b> <code>channel_id or @username</code>\n"
    "Remove a previously added force-sub channel.\n\n"
    
    "/forcesub</b>\n"
    "View the list of currently active force-sub channels with their names and IDs.\n\n"
    "🔧 Made with <b>@lgrambot</b>"
)


    await message.reply_text(help_text)

@Client.on_message(filters.command("addfsub") & filters.private)
async def add_fsub(client: Client, message: Message):
    me = await client.get_me()
    bot_data = bots_collection.find_one({"bot_id": me.id})

    if not bot_data or message.from_user.id != bot_data.get("owner_id"):
        return await message.reply_text("Only the bot owner can add fsub channels.")

    try:
        chat_id = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("This is how you should use it /addfsub <chat_id or @username>")

    try:
        member = await client.get_chat_member(chat_id, me.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("I'm not an admin in that chat. Please promote me.")
    except ChatAdminRequired:
        return await message.reply_text("I'm not an admin there.")
    except Exception as e:
        return await message.reply_text(f"Error this means the bot cant find the chat so send a message on it and come back")

    bots_collection.update_one(
        {"bot_id": me.id},
        {"$addToSet": {"force_sub": chat_id}}
    )

    await message.reply_text("Channel added to force-sub list.")


@Client.on_message(filters.command("delfsub") & filters.private)
async def del_fsub(client: Client, message: Message):
    me = await client.get_me()
    bot_data = bots_collection.find_one({"bot_id": me.id})

    if not bot_data or message.from_user.id != bot_data.get("owner_id"):
        return await message.reply_text("Only the bot owner can remove fsub channels.")

    try:
        chat_id = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("This is how u should use /delfsub chat id or @username>")

    bots_collection.update_one(
        {"bot_id": me.id},
        {"$pull": {"force_sub": chat_id}}
    )

    await message.reply_text("Channel removed from force-sub list.")


@Client.on_message(filters.command("forcesub") & filters.private)
async def show_fsub(client: Client, message: Message):
    me = await client.get_me()
    bot_data = bots_collection.find_one({"bot_id": me.id})

    if not bot_data or message.from_user.id != bot_data.get("owner_id"):
        return await message.reply_text("Only the bot owner can view fsub channels.")

    channels = bot_data.get("force_sub", [])
    if not channels:
        return await message.reply_text("No force-sub channels set.")

    msg = "<b>Current Force-Sub Channels:</b>\n\n"
    for i, ch_id in enumerate(channels, start=1):
        try:
            chat = await client.get_chat(ch_id)
            name = chat.title or "Unnamed"
            msg += f"{i}. <b>{name}</b> - <code>{ch_id}</code>\n"
        except Exception as e:
            msg += f"{i}. <code>{ch_id}</code> - <i>Cannot fetch name</i>\n"

    await message.reply_text(msg)


@Client.on_callback_query(filters.regex("check_fsub"))
async def check_fsub(client, callback_query):
    message = callback_query.message
    user_id = callback_query.from_user.id
    me = await client.get_me()
    bot_data = bots_collection.find_one({"bot_id": me.id})

    if not bot_data:
        return await message.edit_text("Bot not found in database.")

    fsub_channels = bot_data.get("force_sub", [])
    not_joined = []

    for chat_id in fsub_channels:
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                not_joined.append(chat_id)
        except:
            not_joined.append(chat_id)

    if not_joined:
        return await callback_query.answer("Still not joined all channels.", show_alert=True)

    users_collection.update_one(
        {"user_id": user_id, "bot_id": me.id},
        {"$set": {"user_id": user_id, "bot_id": me.id}},
        upsert=True
    )

    custom_message = bot_data.get("start_message", "Hello! I'm alive.")
    await message.edit_text(custom_message)

@Client.on_message(filters.private)
async def promo_reply(client, message):
    me = await client.get_me()
    bot_data = bots_collection.find_one({"bot_id": me.id})

    if not bot_data:
        return
    if message.from_user.id == bot_data.get("owner_id"):
        return

    try:
        await message.reply_text("🤖 Created with @Lgramcreatorbot")
    except:
        pass

