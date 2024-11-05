import re
from constants import *

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from typing import Optional, Tuple
import os

from datetime import datetime
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

from handleJoinOrRemoveFromChat import greet_chat_members
from handlePhotoMessage import handle_photo_message
from handleTextMessage import handle_text_message
from handleVideoMessage import handle_video_message


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Enter the text you want to show to the user whenever they start the bot")
    print(update)


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
    application.add_handler(MessageHandler(filters.TEXT, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video_message))

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
