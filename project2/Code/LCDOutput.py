import RPi.GPIO as GPIO
import time
import requests
import http.client
import urllib
import json
import socket

# a library supports LCD
import LCD1602


# finite state machine state
class FSM():
    chooseNum = 0
    chooseCur = 1
    chooseHis = 2
    numIsChoosed = 3
    curIsChoosed = 4
    hisIsChoosed = 5
    enterDate = 6
    enterTime = 7
    preEnterTime = 8


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


# print words on LCD
def printOnLCD(rowA, rowB):
    LCD1602.clear()
    LCD1602.write(0, 0, rowA)
    LCD1602.write(0, 1, rowB)


# when deciding date, print date data on LCD
def showDate(date, dateCur):
    rowA = "Date: " + str(date[0]) + str(date[1]) + \
        "/" + str(date[2]) + str(date[3]) + "     "
    if (dateCur < 2):
        rowB = "      " + " " * dateCur + "^" + " " * (9 - dateCur)
    else:
        rowB = "       " + " " * dateCur + "^" + " " * (8 - dateCur)
    printOnLCD(rowA, rowB)


# change date with boundary
def addDate(date, dateCur):
    if dateCur == 0:
        date[0] = (date[0] + 1) % 2
    elif dateCur == 1:
        if date[0] == 1:
            date[1] = (date[1] + 1) % 3
        else:
            date[1] = date[1] % 9 + 1
    elif dateCur == 2:
        date[2] = (date[2] + 1) % 4
    else:
        if date[2] == 0:
            date[3] = date[3] % 9 + 1
        elif date[2] == 3:
            date[3] = (date[3] + 1) % 2
        else:
            date[3] = (date[3] + 1) % 10


# when deciding time, print time data on LCD
def showTime(tim, timCur):
    rowA = "Time: " + str(tim[0]) + str(tim[1]) + \
        ":" + str(tim[2]) + str(tim[3]) + "     "
    if (timCur < 2):
        rowB = "      " + " " * timCur + "^" + " " * (9 - timCur)
    else:
        rowB = "       " + " " * timCur + "^" + " " * (8 - timCur)
    printOnLCD(rowA, rowB)


# change time with boundary
def addTime(time, timCur):
    if timCur == 0:
        tim[0] = (tim[0] + 1) % 3
    elif timCur == 1:
        if tim[0] == 2:
            tim[1] = (tim[1] + 1) % 4
        else:
            tim[1] = (tim[1] + 1) % 10
    elif timCur == 2:
        tim[2] = (tim[2] + 1) % 6
    else:
        tim[3] = (tim[3] + 1) % 10


# check whether button is pressed or not
def isButPressed(butState, preButState):
    return butState != preButState


# show the data downloaded from cloud
def showRecord(chnId, deviceId, deviceKey, history):
    data = []
    for i in range(4):
        data.append(
            getToMCS(chnId[i], deviceId, deviceKey, history))

    printOnLCD("A Court:    " + str(data[0]) + "  " + str(data[1]),
               "B Court:    " + str(data[2]) + "  " + str(data[3]))


# show the data downloaded from cloud
def showNumOfPeople(chnId, deviceId, deviceKey, history):
    data = [getToMCS(chnId[0], deviceId, deviceKey, history)]
    len = 1
    while 1:
        if data[0] // len != 0:
            len += 1
        else:
            break
    printOnLCD("Number of People", str(data[0]) + " " * (16 - len))


# cause that downloading historitic record with http "end" parameter uses time data in seconds mode, we use library to transform it
def transportTime(date, tim):
    timeString = ""
    for i in range(4):
        timeString += str(date[i])
    for i in range(4):
        timeString += str(tim[i])
    structTime = time.strptime(
        "2020" + timeString + "00", "%Y%m%d%H%M%S")
    timeStamp = int(time.mktime(structTime))
    return timeStamp


if __name__ == '__main__':
    butPin = [11, 12]

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(butPin[0], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(butPin[1], GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # not real Id and Key
    deviceId = "no hacking"
    deviceKey = "no hacking"

    LCD1602.init(0x27, 1)
    printOnLCD("Welcome to      ", "    Project 3   ")
    time.sleep(3)

    state = FSM()

    try:
        LCD1602.clear()
        try:
            while True:
                printOnLCD("Check Court     ", "Press btn1 start")

                butState = [GPIO.input(butPin[0]), GPIO.input(butPin[1])]
                preButState = butState

                p = state.chooseHis
                date = [0, 1, 0, 1]
                dateCur = 0
                tim = [0, 0, 0, 0]
                timCur = 0

                while True:
                    preButState = butState
                    butState = [GPIO.input(butPin[0]), GPIO.input(butPin[1])]

                    if (isButPressed(butState[0], preButState[0]) and (p == state.chooseCur or p == state.chooseHis or p == state.chooseNum)):
                        if p == state.chooseCur:
                            printOnLCD("History        <", "Num of People   ")
                            p = state.chooseHis
                        elif p == state.chooseHis:
                            printOnLCD("Num of People  <", "Current         ")
                            p = state.chooseNum
                        else:
                            printOnLCD("Current        <", "History         ")
                            p = state.chooseCur
                    elif (isButPressed(butState[1], preButState[1]) and (p == state.chooseCur or p == state.chooseHis or p == state.chooseNum)):
                        if p == state.chooseCur:
                            p = state.curIsChoosed
                            dataChnId = ["A_court_1", "A_court_2",
                                         "B_court_1", "B_court_2"]
                            showRecord(dataChnId, deviceId, deviceKey, "")
                        elif p == state.chooseHis:
                            p = state.hisIsChoosed
                            printOnLCD("Choose Date     ", "Press but1 start")
                        else:
                            p = state.numIsChoosed
                            dataChnId = ["Number_of_people"]
                            showNumOfPeople(dataChnId, deviceId, deviceKey, "")
                    elif isButPressed(butState[0], preButState[0]) and p == state.hisIsChoosed:
                        p = state.enterDate
                        showDate(date, dateCur)
                    elif isButPressed(butState[0], preButState[0]) and p == state.enterDate:
                        addDate(date, dateCur)
                        showDate(date, dateCur)
                    elif isButPressed(butState[1], preButState[1]) and p == state.enterDate:
                        if (dateCur == 3):
                            p = state.preEnterTime
                            printOnLCD("Choose Time     ", "Press but1 start")
                        else:
                            dateCur += 1
                            showDate(date, dateCur)
                    elif isButPressed(butState[0], preButState[0]) and p == state.preEnterTime:
                        p = state.enterTime
                        showTime(tim, timCur)
                    elif isButPressed(butState[0], preButState[0]) and p == state.enterTime:
                        addTime(tim, timCur)
                        showTime(tim, timCur)
                    elif isButPressed(butState[1], preButState[1]) and p == state.enterTime:
                        if (timCur == 3):
                            p = state.curIsChoosed

                            timeStamp = transportTime(date, tim)
                            history = "?end=" + str(timeStamp * 1000)
                            dataChnId = ["A_court_1_occupy", "A_court_2_occupy",
                                         "B_court_1_occupy", "B_court_2_occupy"]
                            showRecord(dataChnId, deviceId, deviceKey, history)
                        else:
                            timCur += 1
                            showTime(tim, timCur)
                    elif isButPressed(butState[1], preButState[1]) and (p == state.curIsChoosed or p == state.numIsChoosed):
                        break
        except KeyboardInterrupt:
            print("Close Program")
            GPIO.cleanup()
    except KeyboardInterrupt:
        print("Close Program")
        GPIO.cleanup()
    finally:
        LCD1602.clear()
