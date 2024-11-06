import psycopg2
from telegram import Update
from telegram.ext import (
    CallbackContext,
)
from datetime import datetime
from constants import *


async def delete_video_message(cursor, update, reason_for_deletion):
    video = update.message.video
    file = await video.get_file()

    file_path = f"{name_dir_videos}/{video.file_id}.{video.mime_type.split('/')[1]}"
    await file.download_to_drive(file_path)

    cursor.execute(sqlInsertDeletedMessages
                   .format(update.message.from_user.id,
                           f"'{datetime.now()}'",
                           "'VIDEO'",
                           f"'{file_path}'",
                           f"'{reason_for_deletion}'"))

    await update.message.delete()


async def handle_video_message(update: Update, context: CallbackContext):
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
        await delete_video_message(cursor, update, error_message_send_video_less_an_hour)

    conn.close()
