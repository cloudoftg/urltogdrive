#!/usr/bin/env python3
import requests
import json
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
from telegram import ParseMode
from telegram.ext.dispatcher import run_async
import os
import sys
from upload import upload
from creds import Creds
from pySmartDL import SmartDL
from pydrive.auth import GoogleAuth

from plugins import TEXT

from plugins.tok_rec import is_token
from time import time
import subprocess
from plugins.dpbox import DPBOX
from plugins.wdl import wget_dl
import re
from mega import Mega

gauth = GoogleAuth()


######################################################################################

bot_token = Creds.TG_TOKEN
updater = Updater(token=bot_token,  workers = 8 , use_context=True)
dp = updater.dispatcher                                                          #
#

######################################################################################


@run_async
def help(update, context):
    try:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=TEXT.HELP, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(e)
# command ```auth```
@run_async
def auth(update, context):
    FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'
    drive: GoogleDrive
    http = None
    initial_folder = None
    ID = update.message.from_user.id
    ID = str(ID)
    try:
        gauth.LoadCredentialsFile(ID)
    except Exception as e:
        print("Cred file missing :", e)

    if gauth.credentials is None:
        authurl = gauth.GetAuthUrl()

        AUTH = TEXT.AUTH_URL.format(authurl)
        context.bot.send_message(
            chat_id=update.message.chat_id, text=AUTH, parse_mode=ParseMode.HTML)

    elif gauth.access_token_expired:
        # Refresh Token if expired
        gauth.Refresh()
    else:
        # auth with  saved creds
        gauth.Authorize()
        context.bot.send_message(
            chat_id=update.message.chat_id, text=TEXT.ALREADY_AUTH)


# It will handle Sent Token By Users
@run_async
def token(update, context):
    msg = update.message.text
    ID = update.message.from_user.id
    ID = str(ID)

    if is_token(msg):
        token = msg.split()[-1]
        print(token)
        try:
            gauth.Auth(token)
            gauth.SaveCredentialsFile(ID)
            context.bot.send_message(
                chat_id=update.message.chat_id, text=TEXT.AUTH_SUCC)
        except Exception as e:
            print("Auth Error :", e)
            context.bot.send_message(chat_id=update.message.chat_id,
                                     text=TEXT.AUTH_ERROR)
   

# command `Start`
@run_async
def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text=TEXT.START.format(update.message.from_user.first_name), parse_mode=ParseMode.HTML)

# command `revoke`
@run_async
def revoke_tok(update, context):
    ID = update.message.chat_id
    ID = str(ID)
    try:
        os.remove(ID)
        context.bot.send_message(
            chat_id=update.message.chat_id, text=TEXT.REVOKE_TOK)
    except Exception as e:
        print(e)
        context.bot.send_message(
            chat_id=update.message.chat_id, text=TEXT.REVOKE_FAIL)

# It will Handle Sent Url
async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] \nP: {2}%\n".format(
            ''.join(["█" for i in range(math.floor(percentage / 5))]),
            ''.join(["░" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text="{}\n {}".format(
                    ud_type,
                    tmp
                )
            )
        except:
            pass


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

@run_async
def UPLOAD(update, context):
    url = update.message.text
    url = url.split()[-1]
    sent_message = context.bot.send_message(
        chat_id=update.message.chat_id, text=TEXT.PROCESSING)

    ID = update.message.chat_id
    ID = str(ID)
    os.path.isfile(ID)
    if os.path.isfile(ID):
        # Openlaod Stuffs

        # I will Add This Later
        if "openload" in url or "oload" in url:
            
            DownloadStatus = False
            sent_message.edit_text("Openload No longer avalible")
            return
        
            # Here is DropBox Stuffs
        elif 'dropbox.com' in url:

            url = DPBOX(url)
            filename = url.split("/")[-1]
            print("Dropbox link Downloading Started : {}".format(
                url.split("/")[-1]))
            sent_message.edit_text(TEXT.DP_DOWNLOAD)
            # filename = wget.download(url)
            filename = wget_dl(str(url))
            print("Downloading Complete : {}".format(filename))
            sent_message.edit_text(TEXT.DOWN_COMPLETE)
            DownloadStatus = True
           # Here IS Mega Links stuffs
        elif 'mega.nz' in url:

            try:
                print("Downlaoding Started")
                sent_message.edit_text(TEXT.DOWN_MEGA)
                m = Mega.from_credentials(TEXT.MEGA_EMAIL, TEXT.MEGA_PASSWORD)
                filename = m.download_from_url(url)
                print("Downloading Complete Mega :", filename)
                sent_message.edit_text(TEXT.DOWN_COMPLETE)

                DownloadStatus = True
            except Exception as e:
                print("Mega Downloding Error :", e)
                sent_message.edit_text("Mega Downloading Error !!")

        else:
            try:
                filename = url.split("/")[-1]

                print("Downloading Started : {}".format(url.split("/")[-1]))
                sent_message.edit_text(TEXT.DOWNLOAD)
                # filename = wget.download(url)
                filename = wget_dl(str(url))
                print("Downloading Complete : {}".format(filename))
                sent_message.edit_text(TEXT.DOWN_COMPLETE)
                DownloadStatus = True
              

            except Exception as e:
                # switch To second download(SmartDl Downloader) `You can activate it throungh TEXT file`
                if TEXT.DOWN_TWO:
                    print(TEXT.DOWN_TWO)
                    try:
                        sent_message.edit_text(
                            "Downloader 1 Error:{} \n\n Downloader 2 :Downloading Started...".format(e))

                        obj = SmartDL(url)
                        obj.start()
                        filename = obj.get_dest()
                        DownloadStatus = True
                    except Exception as e:
                        print(e)
                        sent_message.edit_text(
                            "Downloading error :{}".format(e))
                        DownloadStatus = False
                else:
                    print(e)
                    sent_message.edit_text("Downloading error :{}".format(e))
                    DownloadStatus = False

            # Checking Error Filename
        if "error" in filename:
                # print(filename)
                # print(filename[0],filename[-1],filename[1])
            sent_message.edit_text("Downloading Error !! ")
            os.remove(filename[-1])

            ##########Uploading part  ###################
        try:

            if DownloadStatus:
                sent_message.edit_text(TEXT.UPLOADING)
            try:
                
                await message.edit(
                    text="{}\n {}".format(
                        ud_type,
                        tmp
                    )
                )
            except:
                pass
                SIZE = (os.path.getsize(filename))/1048576
                SIZE = round(SIZE)
                FILENAME = filename.split("/")[-1]
                
                try:
                    FILELINK = upload(filename, update,
                                      context, TEXT.drive_folder_name)
                except Exception as e:
                    print("error Code : UPX11", e)
                    sent_message.edit_text("Uploading fail :{}".format(e))
                else:
                    sent_message.edit_text(TEXT.DOWNLOAD_URL.format(
                        FILENAME, SIZE, FILELINK), parse_mode=ParseMode.HTML)
                print(filename)
                try:
                    os.remove(filename)
                except Exception as e:
                    print(e)
        except Exception as e:
            print("Error code UXP12", e)
            if DownloadStatus:
                sent_message.edit_text("Uploading fail : {}".format(e))
                try:
                    os.remove(filename)
                except Exception as e:
                    print("Error code UXP13", e)
            else:
                sent_message.edit_text("Uploading fail :", e)

    else:
        context.bot.send_message(
            chat_id=update.message.chat_id, text=TEXT.NOT_AUTH)

def status(update, context):
    context.bot.send_message(
        chat_id=update.message.chat_id, text=TEXT.UPDATE, parse_mode=ParseMode.HTML)


update_status = CommandHandler('update', status)
dp.add_handler(update_status)

start_handler = CommandHandler('start', start)
dp.add_handler(start_handler)

downloader_handler = MessageHandler(Filters.regex(r'http'), UPLOAD)
dp.add_handler(downloader_handler)

help_handler = CommandHandler('help', help)
dp.add_handler(help_handler)

auth_handler = CommandHandler('auth', auth)
dp.add_handler(auth_handler)

token_handler = MessageHandler(Filters.text, token)
dp.add_handler(token_handler)

revoke_handler = CommandHandler('revoke', revoke_tok)
dp.add_handler(revoke_handler)


updater.start_polling()
updater.idle()
