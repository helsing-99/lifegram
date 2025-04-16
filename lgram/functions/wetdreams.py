import asyncio
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
import html
from lgram import app
from pymongo import MongoClient
from strings.string import (
    start_command_instructions, help_text, privacy_policy_text
)

from pyrogram.enums import ChatMemberStatus

from config import MONGO_URI, MONGO_DB_NAME

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["cloned"]
bots_collection = mongo_db["bots"]
users_collection = mongo_db["users"]

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    data = callback_query.data

    if data == "help_command":
        buttons = [
            [InlineKeyboardButton("Configure Commands", callback_data="admin_help")],
            [InlineKeyboardButton("Create clone", callback_data="clone_steps")],
            [InlineKeyboardButton("Privacy policy", callback_data="privacy_policy")],
            
            
        ]
        await callback_query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "clone_steps":
        await callback_query.message.edit_text(
"""To clone a bot. follow these steps:\n

Go to @BotFather on Telegram.\n
Use the `/newbot` command to create a new bot and get the bot token.\n

Forward it to this bot from @botfather with tag.\n
Once cloned, you can manage your bot via this bot, and it will work just like the original.\n
If you need to delete a cloned bot, use `/deleteclone` <bot_token>
                             """,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙", callback_data="help_command")]]
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    elif data == "privacy_policy":
        buttons = [
            [InlineKeyboardButton("What Information We Collect", callback_data="info_collect")],
            [InlineKeyboardButton("Why We Collect", callback_data="why_collect")],
            [InlineKeyboardButton("What We Do Not Do", callback_data="what_we_do_not_do")],
            [InlineKeyboardButton("Right to Process", callback_data="right_to_process")],
            [InlineKeyboardButton("🔙", callback_data="help_command")],
        ]
        await callback_query.message.edit_text(
            privacy_policy_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "info_collect":
        text = """
We collect the following user data:\n
- First Name
- Last Name
- Username
- User ID
- Bot token
- force sub channel details
- users id 
- subscribers id
- Clone bot token which is protected by our security features."""
        back_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙", callback_data="privacy_policy")]]
        )
        await callback_query.message.edit_text(
            text,
            reply_markup=back_button,
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "why_collect":
        text = """
We collect it for managing clone bots and avoiding spammers from groups and make chat clean
Also we use it for bot statistics"""
        back_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙", callback_data="privacy_policy")]]
        )
        await callback_query.message.edit_text(
            text,
            reply_markup=back_button,
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "what_we_do_not_do":
        text = """
We do not sell your data to third party"""
        back_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙", callback_data="privacy_policy")]]
        )
        await callback_query.message.edit_text(
            text,
            reply_markup=back_button,
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "right_to_process":
        text = """
You have all rights to process your data on this bot
If you want to delete your data contact @Drxew
Warning: 
While we delete your data all your bots and bot settings will be lost from db."""
        back_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙", callback_data="privacy_policy")]]
        )
        await callback_query.message.edit_text(
            text,
            reply_markup=back_button,
            parse_mode=ParseMode.MARKDOWN
        )     

    elif data == "admin_help":
        text = """
Owner Commands Guide

Use these commands to fully manage your cloned bot:
/setstart Your start message
Set or update the custom message users see when they press /start.
/broadcast Your message
Send a message to all users who have started your bot.
/addfsub channel_id or @username
Add a channel or group where users must be a member to use the bot.
/delfsub channel_id or @username
Remove a previously added force-sub channel.
/forcesub 
View the list of currently active force-sub channels with their names and IDs.
Made with <b>@lgrambo
    """
        back_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙", callback_data="help_command")]]
        )
        await callback_query.message.edit_text(
            text,
            reply_markup=back_button,
            parse_mode=ParseMode.MARKDOWN
        )     

@app.on_message(filters.command("start"))
async def privacy_command(client, message):
    user = message.from_user
    support_channel = "@drxew" 

    try:
        member = await client.get_chat_member(support_channel, user.id)
        if member.status in ("kicked", "left"):
            raise Exception("User not subscribed")
    except Exception:
        invite_link = await client.create_chat_invite_link(support_channel, creates_join_request=False)
        me = await client.get_me()
        bot_username = me.username


        return await message.reply_text(
    "🚫 You must join our support & updates channel to use this bot.\n\n"
    "Please join and then verify your membership.",
    reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Join Support Channel", url=invite_link.invite_link)],
            [InlineKeyboardButton("✅ Verify Membership", url=f"https://t.me/{bot_username}?start=verify")]
        ]
    )
)
    me = await client.get_me()
    users_collection.update_one(
        {"user_id": user.id, "bot_id": me.id},
        {"$set": {"user_id": user.id, "bot_id": me.id}},
        upsert=True
    )

    Help_button = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Configure your bot & more", callback_data="help_command")],
            [InlineKeyboardButton("Create your own bot", callback_data="clone_steps")],
            [InlineKeyboardButton("Support & Updates", url=f"https://t.me/{support_channel.strip('@')}")]
        ]
    )
    await message.reply_text(
        start_command_instructions,
        reply_markup=Help_button
    )



from pyrogram.types import Message

@app.on_callback_query(filters.regex("check_fsub"))
async def check_fsub_main(client, callback_query):
    support_channel = "@drxew"
    user_id = callback_query.from_user.id

    try:
        member = await client.get_chat_member(support_channel, user_id)
        if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            raise Exception("Not subscribed")
    except:
        return await callback_query.answer("🚫 You still haven't joined the support channel.", show_alert=True)

    await callback_query.answer("✅ Subscription verified!")

    try:
        await callback_query.message.delete()
    except:
        pass

    fake_message = Message(
        id=callback_query.message.message_id,
        from_user=callback_query.from_user,
        chat=callback_query.message.chat,
        text="/start"
    )
    await privacy_command(client, fake_message)

SUDO_USERS = [137799257]

@app.on_message(filters.command("broadcast") & filters.private)
async def main_broadcast_handler(client, message):
    if message.from_user.id not in SUDO_USERS:
        return await message.reply_text("🚫 You are not authorized to use this command.")

    me = await client.get_me()
    try:
        broadcast_text = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text(
            "Please provide a message to broadcast.\n\nExample:\n<code>/broadcast Hello everyone!</code>",
            parse_mode="html"
        )

    users = users_collection.find({"bot_id": me.id})
    total = 0
    success = 0
    failed = 0

    status = await message.reply_text(" Broadcasting started...")

    for user in users:
        user_id = user.get("user_id")
        total += 1
        try:
            await client.send_message(user_id, broadcast_text)
            success += 1
        except:
            failed += 1

    await status.edit_text(
        f"<b>Broadcast Finished</b>\n\n"
        f"Total Users: <code>{total}</code>\n"
        f"Sent: <code>{success}</code>\n"
        f"Failed: <code>{failed}</code>",
        parse_mode="html"
    )
