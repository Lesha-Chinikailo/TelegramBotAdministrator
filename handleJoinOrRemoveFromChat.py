from datetime import datetime
from typing import Optional, Tuple

import psycopg2
from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)

from constants import *


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

        now = datetime.now()
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