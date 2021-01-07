from __future__ import unicode_literals
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import time
import requests
import http.client
import urllib
import json
import socket
import configparser

app = Flask(__name__)

# basic information for line bot
# in short, we store the data in config.ini, and read from it
# it's a better way that we can control the data when the scale is large
config = configparser.ConfigParser()
config.read('config.ini')
# create an objest, we use function "reply_message()"
# "reply_message()" can only reply exactly once receiving each message, it can tell by reply_token
line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

# MCS id and key
deviceId = "noHacking"
deviceKey = "noHacking"


class FSM():
    choose = 0
    enterDate = 1
    enterTime = 2


# get data from cloud, add history parameter to get historitic record
def getToMCS(channel, deviceId, deviceKey, history):
    host = "http://api.mediatek.com"
    endPoint = "/mcs/v2/devices/" + deviceId + \
        "/datachannels/" + channel + "/datapoints"
    url = host + endPoint + history

    headers = {"Content-type": "application/json", "deviceKey": deviceKey}
    r = requests.get(url, headers=headers)
    value = (r.json()["dataChannels"][0]["dataPoints"][0]["values"]["value"])
    return value


# cause that downloading historitic record with http "end" parameter uses time data in mili-seconds mode, we use library to transform it
def transportTime(date, tim):
    timeString = date + tim

    structTime = time.strptime(
        timeString + "00", "%Y/%m/%d%H:%M%S")
    timeStamp = int(time.mktime(structTime))
    return timeStamp * 1000


# post information to /callback to comfirm the identity and order what to do
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        print(body, signature)
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'


def isNum(str):
    for it in str:
        if it < '0' or it > '9':
            return 0
    return 1


def chkDate(date):
    print ("\n\n\n", date)
    if len(date) != 10 or (isNum(date[0:4])) == 0 or (int)(date[0:4]) > 2021 or (int)(date[0:4]) < 0 or date[4] != '/' or (isNum(date[5:7])) == 0 or (int)(date[5:7]) > 12 or (int)(date[5:7]) < 1 or date[7] != '/' or (isNum(date[8:10])) == 0 or (int)(date[8:10]) > 31 or (int)(date[8:10]) < 1:
        return 0
    return 1


def chkTim(tim):
    if len(tim) != 5 or (isNum(tim[0:2])) == 0 or (int)(tim[0:2]) > 23 or (int)(tim[0:2]) < 0 or tim[2] != ':' or (isNum(tim[3:5])) == 0 or (int)(tim[3:5]) > 59 or (int)(tim[3:5]) < 0:
        return 0
    return 1


def replyChoose(event):
    send = "球場查詢 Line Bot 指令:\n" + \
           "球場人數　　　查詢球場內人數\n" + \
           "現行使用狀態　查詢即時球場使用狀態\n" + \
           "使用紀錄　　　查詢球場使用狀態的歷史紀錄"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=send)
    )


def replyNum(event):
    data = [getToMCS("Number_of_people", deviceId, deviceKey, "")]
    send = "球場內人數:    " + str(data[0])
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=send)
    )


def replyCur(event):
    dataChnId = ["A_court_1", "A_court_2",
                 "B_court_1", "B_court_2"]
    data = []
    used = ["閒置中", "使用中"]
    for i in range(4):
        data.append(
            getToMCS(dataChnId[i], deviceId, deviceKey, ""))
    send = "A1 Court:    " + used[data[0]] + "\n" + "A2 Court:    " + used[data[1]] + "\n" + \
           "B1 Court:    " + used[data[2]] + "\n" + \
        "B2 Court:    " + used[data[3]]
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=send)
    )


p = 0
state = FSM()
date = ""
tim = ""


# act when MessageEvent appears and the message's type is "TextMessage"
@handler.add(MessageEvent, message=TextMessage)
def interact(event):
    global p, date, tim

    if p == state.choose:
        if event.message.text == "球場人數":
            replyNum(event)
        elif event.message.text == "現行使用狀態":
            replyCur(event)
        elif event.message.text == "使用紀錄":
            p = state.enterDate
        else:
            replyChoose(event)

    if p == state.enterDate:
        if event.message.text == "退出":
            p = state.choose
            replyChoose(event)
        elif chkDate(event.message.text):
            p = state.enterTime
            date = event.message.text
        else:
            send = "使用紀錄查詢 Line Bot 指令:\n" + \
                   "yyyy/mm/dd　按格式輸入欲查詢日期\n" + \
                   "退出　　　　 退出使用紀錄查詢"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=send)
            )

    if p == state.enterTime:
        if event.message.text == "退出":
            p = state.choose
            replyChoose(event)
        elif chkTim(event.message.text):
            p = state.choose
            tim = event.message.text
            timeStamp = transportTime(date, tim)
            history = "?end=" + str(timeStamp)
            dataChnId = ["A_court_1_occupy", "A_court_2_occupy",
                         "B_court_1_occupy", "B_court_2_occupy"]
            data = []
            used = ["閒置中", "使用中"]
            for i in range(4):
                data.append(
                    getToMCS(dataChnId[i], deviceId, deviceKey, history))
            send = date + " " + tim + "\n" + "A1 Court:    " + used[data[0]] + "\n" + "A2 Court:    " + used[data[1]] + "\n" + \
                "B1 Court:    " + used[data[2]] + \
                "\n" + "B2 Court:    " + used[data[3]]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=send)
            )
        else:
            send = "使用紀錄查詢 Line Bot 指令:\n" + \
                   "hh:mm　　按格式輸入欲查詢時間\n" + \
                   "退出　   退出使用紀錄查詢"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=send)
            )


if __name__ == "__main__":
    app.run()
