import os
from dotenv import load_dotenv, find_dotenv

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