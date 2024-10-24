import re

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from typing import Optional, Tuple
import os
import psycopg2
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timezone

from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    Updater,
    CallbackContext,
)
import datetime
import psycopg2

# sqlInsert = """INSERT INTO dateJoined(id, datetime)
#              VALUES({}, {})"""
#
# sqlSelect = """Select datetime FROM dateJoined
#              WHERE id = {}"""
#
# sqlDelete = """Delete FROM dateJoined
#              WHERE id = {}"""

config_path = find_dotenv('config.env')

load_dotenv(config_path)

sqlInsert = os.getenv("sqlInsert")
sqlSelect = os.getenv("sqlSelect")
sqlDelete = os.getenv("sqlDelete")

seconds_in_hour = 60 * 60
seconds_in_day = seconds_in_hour * 24


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Enter the text you want to show to the user whenever they start the bot")
    print(update)


async def handle_message(update: Update, context: CallbackContext):
    conn = psycopg2.connect(database="BotAdministrator",
                            host="localhost",
                            user="postgres",
                            password="postgres",
                            port="5432")
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(sqlSelect.format(update.message.from_user.id))
    datetime_joined_user = cursor.fetchone()[0]
    time_user_is_in_the_chat = datetime.datetime.now() - datetime_joined_user
    if time_user_is_in_the_chat.total_seconds() < seconds_in_hour:
        await update.message.delete()
    elif re.search("(?P<url>https?://[^\s]+)", update.message.text):
        if time_user_is_in_the_chat.total_seconds() < seconds_in_day:
            await update.message.delete()


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    new_user = update.chat_member.new_chat_member.user

    conn = psycopg2.connect(database="BotAdministrator",
                            host="localhost",
                            user="postgres",
                            password="postgres",
                            port="5432")
    conn.autocommit = True
    cursor = conn.cursor()
    # cursor.execute("SELECT * FROM DateJoined")
    # print(cursor.fetchone())

    if not was_member and is_member:
        await update.effective_chat.send_message(
            f"{member_name} was added by {cause_name}. Welcome!",
            parse_mode=ParseMode.HTML,
        )

        now = datetime.datetime.now()
        cursor.execute(sqlInsert.format(new_user.id, f"'{now}'"))
    elif was_member and not is_member:
        await update.effective_chat.send_message(
            f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...",
            parse_mode=ParseMode.HTML,
        )
        cursor.execute(sqlSelect.format(new_user.id))
        # datetime_user = cursor.fetchone()
        # print(datetime_user[0])
        # print(datetime.datetime.now() - datetime_user[0])
        cursor.execute(sqlDelete.format(new_user.id))

    conn.close()


def main() -> None:
    application = Application.builder().token(os.getenv("TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

# def check_message(update: Update, context: CallbackContext) -> None:
#     message = update.message
#
#     if message.entities:
#         for entity in message.entities:
#             if entity.type == 'url':
#                 user_join_time = message.from_user.date
#                 current_time = datetime.datetime.now(datetime.timezone.utc)
#
#                 if (current_time - user_join_time).total_seconds() < 86400:
#                     context.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
#                     break
