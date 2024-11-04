import re
import os

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from typing import Optional, Tuple
import os
import psycopg2
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timezone
from PIL import Image

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

config_path = find_dotenv('config.env')

load_dotenv(config_path)

sqlInsertDateJoined = os.getenv("sqlInsertDateJoined")
sqlSelectDateJoined = os.getenv("sqlSelectDateJoined")
sqlDeleteDateJoined = os.getenv("sqlDeleteDateJoined")

sqlInsertDeletedMessages = os.getenv("sqlInsertDeletedMessages")

sqlInsertUsers = os.getenv("sqlInsertUsers")
sqlSelectIdUsers = os.getenv("sqlSelectIdUsers")

seconds_in_hour = 60 * 60
seconds_in_day = seconds_in_hour * 24

error_message_send_message_less_days = "user was in chat less than a day and he sent a reference"
error_message_send_photo_less_days = "user was in chat less than a day and he sent a photo"
error_message_send_video_less_days = "user was in chat less than a day and he sent a video"

name_dir_images = "images"
name_dir_videos = "videos"


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Enter the text you want to show to the user whenever they start the bot")
    print(update)


async def delete_text_message(cursor, update: Update, reason_for_deletion: str):
    cursor.execute(sqlInsertDeletedMessages
                   .format(update.message.from_user.id,
                           f"'TEXT'",
                           f"'{update.message.text}'",
                           f"'{reason_for_deletion}'"))

    await update.message.delete()


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


async def handle_message(update: Update, context: CallbackContext):
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
    time_user_is_in_the_chat = datetime.datetime.now() - datetime_joined_user
    if time_user_is_in_the_chat.total_seconds() < seconds_in_hour:
        await delete_text_message(cursor, update, "user was in chat less than an hour")
    elif re.search("(?P<url>https?://[^\s]+)", update.message.text):
        if time_user_is_in_the_chat.total_seconds() < seconds_in_day:
            await delete_text_message(cursor, update, error_message_send_message_less_days)

    conn.close()


async def handle_photo(update: Update, context: CallbackContext):
    conn = psycopg2.connect(database="BotAdministrator",
                            host="localhost",
                            user="postgres",
                            password="postgres",
                            port="5432")
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(sqlSelectDateJoined.format(update.message.from_user.id))
    datetime_joined_user = cursor.fetchone()[0]
    time_user_is_in_the_chat = datetime.datetime.now() - datetime_joined_user
    if time_user_is_in_the_chat.total_seconds() < seconds_in_hour:
        await delete_photo_message(cursor, update, error_message_send_photo_less_days)

    conn.close()


async def delete_video_message(cursor, update, reason_for_deletion):
    video = update.message.video
    file = await video.get_file()

    file_path = f"{name_dir_videos}/{video.file_id}.{video.mime_type.split('/')[1]}"
    await file.download_to_drive(file_path)

    cursor.execute(sqlInsertDeletedMessages
                   .format(update.message.from_user.id,
                           "'VIDEO'",
                           f"'{file_path}'",
                           f"'{reason_for_deletion}'"))

    await update.message.delete()


async def handle_video(update: Update, context: CallbackContext):
    conn = psycopg2.connect(database="BotAdministrator",
                            host="localhost",
                            user="postgres",
                            password="postgres",
                            port="5432")
    conn.autocommit = True
    cursor = conn.cursor()
    await delete_video_message(cursor, update, error_message_send_video_less_days)

    # cursor.execute(sqlSelectDateJoined.format(update.message.from_user.id))
    # datetime_joined_user = cursor.fetchone()[0]
    # time_user_is_in_the_chat = datetime.datetime.now() - datetime_joined_user
    # if time_user_is_in_the_chat.total_seconds() < seconds_in_hour:
    #     await delete_video_message(cursor, update, error_message_send_video_less_days)

    conn.close()


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
        cursor.execute(sqlInsertDateJoined.format(new_user.id, f"'{now}'"))
        cursor.execute(sqlSelectIdUsers.format(new_user.id))
        fetchone = cursor.fetchone()
        if fetchone is None:
            username = new_user.username if new_user.username is not None else "null"
            cursor.execute(sqlInsertUsers.format(
                new_user.id,
                f"'{username}'",
                f"'{new_user.full_name}'"
            ))
    elif was_member and not is_member:
        await update.effective_chat.send_message(
            f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...",
            parse_mode=ParseMode.HTML,
        )
        cursor.execute(sqlSelectDateJoined.format(new_user.id))
        # datetime_user = cursor.fetchone()
        # print(datetime_user[0])
        # print(datetime.datetime.now() - datetime_user[0])
        cursor.execute(sqlDeleteDateJoined.format(new_user.id))

    conn.close()


def main() -> None:
    directory = name_dir_images
    if not os.path.exists(directory):
        os.mkdir(directory)
    directory = name_dir_videos
    if not os.path.exists(directory):
        os.mkdir(directory)
    application = Application.builder().token(os.getenv("TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

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
