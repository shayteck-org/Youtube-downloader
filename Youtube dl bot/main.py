from pyrogram import*
from pyrogram.types import*
from dotenv import *
import sqlite3
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from selenium import *
from selenium.webdriver.common.keys import Keys
import requests
import datetime
from pytube import*
import os
import time
import requests



# STRUCTURE
class Admin:
    def __init__(self):
        load_dotenv()
        self.id = int(os.getenv("admin_id"))
        self.state = ""
        self.channels = []
        self.load_channels()

    def load_channels(self):
        conn = sqlite3.connect('BotData.db')
        cursor = conn.cursor()
        cursor.execute("SELECT channel FROM channels")
        rows = cursor.fetchall()
        self.channels.clear()
        for row in rows:
            self.channels.append(row[0])
        conn.close()

    def add_channel(self, _input):
        conn = sqlite3.connect('BotData.db')
        cursor = conn.cursor()
        _input = _input.replace("@", "")
        cursor.execute("INSERT INTO channels (channel) VALUES (?)", (_input,))
        print(_input, "added successfully!")
        conn.commit()
        conn.close()
        self.load_channels()

    def delete_channel(self, _input):
        conn = sqlite3.connect('BotData.db')
        c = conn.cursor()
        c.execute("DELETE FROM Channels WHERE channel=?", (_input,))
        conn.commit()
        print(_input, "deleted successully!")
        conn.close()
        self.load_channels()


class User:
    def __init__(self, _id, _state, joindate):
        self.id = _id
        self.state = _state
        self.join_date = joindate


def check_link(link):
    if "youtube.com" in link or "youtu.be" in link:
        return True
    else:
        return False


def youtube_download(link, res, message: Message, client: Client):
    sent_message = message.reply_text("در حال بررسی...")
    video_url = link
    yt = YouTube(video_url)
    title = yt.title

    selected_stream = yt.streams.filter(res=res, progressive=True).first()
    sent_message.delete()
    sent_message = message.reply_text("در حال دانلود...")
    selected_stream.download()
    sent_message.delete()

    sent_message = message.reply_text("با موفقیت دانلود شد، در حال ارسال...")
    special_characters = r'\/:*?"<>|#'
    path = ''.join(char for char in title if char not in special_characters) + ".mp4"
    print(path)
    message.reply_video(video=path)
    sent_message.delete()

    os.remove(path=path)
    print(path, "has been successfully deleted.")


def back_button(client: Client, message: Message, text):
    global admin_temp_message
    admin_temp_message = message.reply_text(text, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="بازگشت", callback_data="back")]]
    ))


def join_checker(client: Client, message: Message):
    for channel in admin.channels:
        try:
            user_obj = client.get_chat_member(chat_id=channel, user_id=message.chat.id)
            print(user_obj.status)
            if str(user_obj.status) == "ChatMemberStatus.ADMINISTRATOR":
                return False
        except Exception as e:
            print(e)
            print("exception risen")
            return False
    return True


def users_load():
    conn = sqlite3.connect('BotData.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = []

    for row in cursor.fetchall():
        user = User(_id=row[0], _state=row[1], joindate=row[2])
        users.append(user)
    return users


def users_update(_id, _state, _joindate):
    conn = sqlite3.connect('BotData.db')
    cursor = conn.cursor()
    new_record = (_id, _state, _joindate)
    cursor.execute('INSERT INTO users (id, state, start_date) VALUES (?, ?, ?)', new_record)
    conn.commit()
    conn.close()
    user = User(_id=_id, _state=_state, joindate=_joindate)
    global users
    users.append(user)


def users_search(key):
    for index in range(len(users)):
        if users[index].id == str(key):
            return index
    return None


# CONFIGRATIONS

load_dotenv("config.env")
api_id = os.getenv("api_id")
api_hash = os.getenv("api_hash")
bot_token = os.getenv("bot_token")
bot_name = os.getenv("bot_name")
admin = Admin()
admin_temp_message = None
users = users_load()
join_filter = filters.create(join_checker)
temp_messages = {}
links = {}
app = Client(name=bot_name, api_id=api_id, api_hash=api_hash, bot_token=bot_token)


# MAIN BODY
@app.on_message(filters.command("start"))
def start_handler(client: Client, message: Message):
    if message.from_user.id == admin.id:
        admin.state = "start"
        text = "به ربات خودتان خوش آمدید🌹🙏 \n چه کاری میتوانم برایتان انجام دهم؟"
        message.reply_text(text=text,
                           reply_markup=InlineKeyboardMarkup(
                               [
                                   [InlineKeyboardButton(text="اضافه کردن کانال", callback_data="add channel")],
                                   [InlineKeyboardButton(text="حذف کردن کانال", callback_data="remove channel")]
                               ]
                           ))

    else:
        if join_checker(client=client, message=message):
            if users_search(key=message.from_user.id) is None:
                users_update(_id=message.from_user.id, _state="start", _joindate=str(message.date))
            else:
                print("already in the database, not added")
                users[users_search(message.from_user.id)].state = "start"

            message.reply_text("سلام خوش اومدی! لینک ویدیوی یوتوب مورد نظرتو وارد کن تا فایلشو واست بفرستم.")

        else:
            text = "لطفا برای استفاده از بات تو کانال های ما عضو شو🙏✅ \n"
            for channel in admin.channels:
                text += "@" + channel + "\n"
            message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="عضو شدم", callback_data="join check")]]
            ))


@app.on_callback_query()
def call_back_handler(client: Client, callback: CallbackQuery):
    if callback.data == "add channel":
        admin.state = callback.data
        callback.message.reply_text(
            "آیدی کانالتان را (بدون @) وارد کنید و همچنین مطمئن شوید که بات از قبل در کانال ادمین است 🙂🆔")

    elif callback.data == "remove channel":
        admin.state = callback.data
        channels_temp = []
        if len(admin.channels) == 0:
            back_button(client=client, message=callback.message, text="شما کانالی برای حذف کردن ندارید!")
        else:
            for channel in admin.channels:
                print(channel)
                channels_temp.append([InlineKeyboardButton(text=channel, callback_data=channel)])
            callback.message.reply_text("یکی از کانال هایتان را برای حذف شدن انتخاب کنید❌",
                                        reply_markup=InlineKeyboardMarkup(channels_temp))

    elif callback.data == "join check":
        if join_checker(message=callback.message, client=client):
            txt = "حالا میتونی از امکانات بات استفاده کنی🤝❤️"
            callback.message.reply_text(text=txt)
        else:
            text = "لطفا برای استفاده از بات تو کانال های ما عضو شو🙏. \n"
            for channel in admin.channels:
                text += "@" + channel + "\n"
            callback.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="عضو شدم", callback_data="join check")]]
            ))

    elif callback.data == "back":
        global admin_temp_message
        admin_temp_message.delete()
        admin.state = "start"
        text = "چه کاری میتوانم برایتان انجام دهم؟"
        callback.message.reply_text(text=text,
                                    reply_markup=InlineKeyboardMarkup(
                                        [
                                            [InlineKeyboardButton(text="اضافه کردن کانال",
                                                                  callback_data="add channel")],
                                            [InlineKeyboardButton(text="حذف کردن کانال",
                                                                  callback_data="remove channel")]
                                        ]
                                    ))
    elif callback.data[len(callback.data)-1] == "p" and callback.from_user.id != admin.id:
        temp_messages[callback.from_user.id].delete()
        print("sent to download")
        youtube_download(link=links[callback.from_user.id],res=callback.data, client=client, message=callback.message)
    else:
        if admin.state == "remove channel":
            admin.delete_channel(_input=callback.data)
            back_button(client=client, message=callback.message, text="این کانال با موفقیت حذف شد🫡")


@app.on_message()
def message_handler(client: Client, message: Message):
    if message.from_user.id == admin.id:
        if admin.state == "add channel":
            admin.add_channel(_input=message.text)
            back_button(client=client, message=message, text="کانال با موفقیت ثبت شد🫡")
    else:
        if join_checker(client=client, message=message):
            global temp_messages
            global links
            if check_link(message.text):
                yt = YouTube(message.text)
                print("Available resolutions:")
                resolutions = []
                links[message.from_user.id] = message.text
                for stream in yt.streams.filter(progressive=True):
                    print(stream.resolution)
                    resolution_button = [InlineKeyboardButton(text=stream.resolution, callback_data=stream.resolution)]
                    resolutions.append(resolution_button)
                print("Video qualities exracted.")
                txt = "لطفا یکی از کیفیت های موجود رو انتخاب کن. " + "\n"
                temp_messages[message.from_user.id] = message.reply_text(text=txt,
                                                                        reply_markup=InlineKeyboardMarkup(resolutions))
            else:
                message.reply_text("لینک ارسال شده اشتباه است، لطفا لینک مناسب را ارسال کنید.")
        else:
            text = "لطفا برای استفاده از بات تو کانال های ما عضو شو🙏✅ \n"
            for channel in admin.channels:
                text += "@" + channel + "\n"
            message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="عضو شدم", callback_data="join check")]]
            ))



app.run()
