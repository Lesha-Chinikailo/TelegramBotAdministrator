from datetime import datetime

import psycopg2
from telegram import Update
from telegram.ext import (
    CallbackContext,
)

from constants import *


async def delete_photo_message(cursor, update: Update, reason_for_deletion: str):
    photo = update.message.photo[-1]
    file = await photo.get_file()

    file_path = f"{name_dir_images}/{photo.file_id}.jpg"
    await file.download_to_drive(file_path)

    cursor.execute(sqlInsertDeletedMessages
                   .format(update.message.from_user.id,
                           "'PHOTO'",
                           f"'{file_path}'",
                           f"'{reason_for_deletion}'"))

    await update.message.delete()


async def handle_photo_message(update: Update, context: CallbackContext):
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
        await delete_photo_message(cursor, update, error_message_send_photo_less_days)

    conn.close()