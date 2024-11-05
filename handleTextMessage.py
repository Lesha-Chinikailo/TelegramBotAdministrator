from datetime import datetime

import re
import psycopg2
from telegram import Update
from telegram.ext import (
    CallbackContext,
)

from constants import *


async def delete_text_message(cursor, update: Update, reason_for_deletion: str):
    cursor.execute(sqlInsertDeletedMessages
                   .format(update.message.from_user.id,
                           f"'TEXT'",
                           f"'{update.message.text}'",
                           f"'{reason_for_deletion}'"))

    await update.message.delete()


async def handle_text_message(update: Update, context: CallbackContext):
    chat_admins = await update.effective_chat.get_administrators()
    if update.effective_user in (admin.user for admin in chat_admins):
        print("user is admin")
        return

    conn = psycopg2.connect(database="BotAdministrator",
                            host="localhost",
                            user="postgres",
                            password="postgres",
                            port="5432")
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(sqlSelectDateJoined.format(update.message.from_user.id))
    datetime_joined_user = cursor.fetchone()[0]
    time_user_is_in_the_chat = datetime.now() - datetime_joined_user
    if time_user_is_in_the_chat.total_seconds() < seconds_in_hour:
        await delete_text_message(cursor, update, "user was in chat less than an hour")
    elif re.search("(?P<url>https?://[^\s]+)", update.message.text):
        if time_user_is_in_the_chat.total_seconds() < seconds_in_day:
            await delete_text_message(cursor, update, error_message_send_message_less_days)

    conn.close()