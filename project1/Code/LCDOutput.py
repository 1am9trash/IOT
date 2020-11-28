import RPi.GPIO as GPIO
import LCD1602 # a library supports LCD
import time
import requests
import http.client
import urllib
import json
import socket

# get mcs data
# add input "history" to search history record 
# you need add parameter "start" & "end" to search history 
def get_to_mcs(channel, history):
    host = "http://api.mediatek.com"
    endpoint = "/mcs/v2/devices/" + deviceId + \
        "/datachannels/" + channel + "/datapoints" + history
    url = host + endpoint

    # DEBUG: check URL is valid
    # print(url)

    headers = {"Content-type": "application/json", "deviceKey": deviceKey}
    r = requests.get(url, headers=headers)
    value = (r.json()["dataChannels"][0]["dataPoints"][0]["values"]["value"])
    return value

# post data to mcs
def post_to_mcs(payload):
    headers = {"Content-type": "application/json", "deviceKey": deviceKey}
    not_connected = 1
    while (not_connected):
        try:
            conn = http.client.HTTPConnection("api.mediatek.com:80")
            conn.connect()
            not_connected = 0
        except (http.client.HTTPException, socket.error) as ex:
            print ("Error: %s" % ex)
            time.sleep(10)
    conn.request("POST", "/mcs/v2/devices/" + deviceId +
                 "/datapoints", json.dumps(payload), headers)
    response = conn.getresponse()
    print(response.status, response.reason,
          json.dumps(payload), time.strftime("%c"))
    data = response.read()
    conn.close()

# button output pin in Board meaning
but_1 = 11
but_2 = 12

# MCS device id and key
# it's not our real ID and key
deviceId = "no hacking"
deviceKey = "no hacking"

print("Press Ctrl-C To Stop")

# GPIO setting
GPIO.setmode(GPIO.BOARD)
GPIO.setup(but_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(but_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

LCD1602.init(0x27, 1)
# show start massage
LCD1602.write(0, 0, "Welcome to      ")
LCD1602.write(0, 1, "    Project 2   ")
time.sleep(5)

try:
    LCD1602.clear()
    try:
        while True:
            choose = 1     # choose "current" or "history"
            status = 0     # 0: haven't choose yet, 1: current, 2: history
            enterTim = 0   # 0: haven't choose yet, 1: choose date, 2: choose time

            # use integer to save date and time
            # the prefix two number mean "month" and "hour" respectively
            # the other two number mean "day" and "minute" respectively
            date = 101
            tim = 0

            # "curSelect" means which number is deciding
            curDateSelect = 3
            curTimSelect = 4

            # just like what draw in flow chart, it's the second page to show
            LCD1602.write(0, 0, "Check Court     ")
            LCD1602.write(0, 1, "Press btn1 start")

            # because we choose the button with states (0 or 1)
            # so wether the button is pressed or not need to consider previous state 
            # if (state != prev_state), means that the button is pressed
            but_1_state = GPIO.input(but_1)
            but_2_state = GPIO.input(but_2)
            pre_but_1 = but_1_state
            pre_but_2 = but_2_state

            while True:
                pre_but_1 = but_1_state
                pre_but_2 = but_2_state
                but_1_state = GPIO.input(but_1)
                but_2_state = GPIO.input(but_2)

                # DEBUG: check when button 2 is pressed
                # if pre_but_2 != but_2_state:
                # print("b2", pre_but_2, but_2_state)

                # DEBUG: check whether button 1 work or not
                # payload = {"datapoints": [{"dataChnId": "but_1", "values": {"value": str(int(but_1_state))}}]}
                # post_to_mcs(payload)

                # Choose "current" or "history"
                # 0: curruent, 1: history
                if but_1_state != pre_but_1 and status == 0:
                    if choose == 1:
                        LCD1602.write(0, 0, "Current        <")
                        LCD1602.write(0, 1, "History         ")
                        choose = (choose + 1) % 2
                    else:
                        LCD1602.write(0, 0, "Current         ")
                        LCD1602.write(0, 1, "History        <")
                        choose = (choose + 1) % 2
                    continue

                # button 2 is "enter"
                if but_2_state != pre_but_2 and status == 0:
                    # choose current, get data from mcs, and show
                    if choose == 0:
                        status = 1

                        A_court_1 = get_to_mcs("A_court_1", "")
                        A_court_2 = get_to_mcs("A_court_2", "")
                        B_court_1 = get_to_mcs("B_court_1", "")
                        B_court_2 = get_to_mcs("B_court_2", "")

                        str1 = "A Court: " + \
                            str(A_court_1) + "     " + str(A_court_2)
                        str2 = "B Court: " + \
                            str(B_court_1) + "     " + str(B_court_2)

                        LCD1602.write(0, 0, str(str1))
                        LCD1602.write(0, 1, str(str2))
                    # choose history, need choose date and time, and get history record from mcs
                    else:
                        status = 2
                        LCD1602.write(0, 0, "Choose Date     ")
                        LCD1602.write(0, 1, "Press but1 start")
                    continue

                # choose "history"
                if status == 2:
                    if enterTim == 0 and but_1_state != pre_but_1:
                        # start to decide "date"
                        enterTim = 1
                        LCD1602.write(0, 0, "Date: 01/01     ")
                        LCD1602.write(0, 1, "      ^         ")
                    # decide "date"
                    elif enterTim == 1 and but_1_state != pre_but_1:
                        # consider that if the data reach the upper bound, the next value is reset to lower bound
                        if curDateSelect == 3:
                            if date // 1000 == 1:
                                date -= 1000
                            else:
                                date += 1000
                        elif curDateSelect == 2:
                            if date // 1000 == 1:
                                if date % 1000 // 100 == 2:
                                    date -= 200
                                else:
                                    date += 100
                            else:
                                if date % 1000 // 100 == 9:
                                    date -= 800
                                else:
                                    date += 100
                        elif curDateSelect == 1:
                            if date % 100 // 10 == 3:
                                date -= 30
                            else:
                                date += 10
                        else:
                            if date % 10 == 9:
                                date -= 9
                            else:
                                date += 1

                        month = str(date // 100)
                        if len(month) == 1:
                            month = "0" + month
                        day = str(date % 100)
                        if len(day) == 1:
                            day = "0" + day

                        LCD1602.write(
                            0, 0, "Date: " + month + "/" + day + "     ")
                    elif enterTim == 1 and but_2_state != pre_but_2:
                        curDateSelect -= 1
                        # every number is already decided, change to decide "time"
                        if curDateSelect < 0:
                            enterTim = 2
                            LCD1602.write(0, 0, "Choose Time     ")
                            LCD1602.write(0, 1, "Press but1 start")
                        else:
                            # the symbol "^" show which number you are deciding
                            if curDateSelect == 3:
                                LCD1602.write(0, 1, "      ^         ")
                            elif curDateSelect == 2:
                                LCD1602.write(0, 1, "       ^        ")
                            elif curDateSelect == 1:
                                LCD1602.write(0, 1, "         ^      ")
                            else:
                                LCD1602.write(0, 1, "          ^     ")
                    elif enterTim == 2 and curTimSelect == 4 and but_1_state != pre_but_1:
                        # start to decide "time"
                        curTimSelect = 3
                        LCD1602.write(0, 0, "Time: 00:00     ")
                        LCD1602.write(0, 1, "      ^         ")
                    # same as "date"
                    elif enterTim == 2 and but_1_state != pre_but_1:
                        if curTimSelect == 3:
                            if tim // 1000 == 2:
                                tim -= 2000
                            else:
                                tim += 1000
                        elif curTimSelect == 2:
                            if tim // 1000 == 2:
                                if tim % 1000 // 100 == 3:
                                    tim -= 300
                                else:
                                    tim += 100
                            else:
                                if tim % 1000 // 100 == 9:
                                    tim -= 900
                                else:
                                    tim += 100
                        elif curTimSelect == 1:
                            if tim % 100 // 10 == 5:
                                tim -= 50
                            else:
                                tim += 10
                        else:
                            if tim % 10 == 9:
                                tim -= 9
                            else:
                                tim += 1

                        hour = str(tim // 100)
                        if len(hour) == 1:
                            hour = "0" + hour
                        minu = str(tim % 100)
                        if len(minu) == 1:
                            minu = "0" + minu

                        LCD1602.write(
                            0, 0, "Time: " + hour + ":" + minu + "     ")
                    elif enterTim == 2 and but_2_state != pre_but_2:
                        curTimSelect -= 1
                        if curTimSelect < 0:
                            month = str(date // 100)
                            if len(month) == 1:
                                month = "0" + month
                            day = str(date % 100)
                            if len(day) == 1:
                                day = "0" + day

                            hour = str(tim // 100)
                            if len(hour) == 1:
                                hour = "0" + hour
                            minu = str(tim % 100)
                            if len(minu) == 1:
                                minu = "0" + minu

                            # the "start" and "end" parameter in http use the unix timestamp
                            timeString = "2020" + month + day + hour + minu + "00"
                            structTime = time.strptime(
                                timeString, "%Y%m%d%H%M%S")
                            timeStamp = int(time.mktime(structTime))

                            # DEBUG: check the timestamp is correct
                            # print(timeStamp)

                            # part of URL (the "end" parameter part)
                            history = "?end=" + str(timeStamp * 1000)
                            A_court_1 = get_to_mcs("A_court_1_occupy", history)
                            A_court_2 = get_to_mcs("A_court_2_occupy", history)
                            B_court_1 = get_to_mcs("B_court_1_occupy", history)
                            B_court_2 = get_to_mcs("B_court_2_occupy", history)

                            str1 = "A Court: " + \
                                str(A_court_1) + "     " + str(A_court_2)
                            str2 = "B Court: " + \
                                str(B_court_1) + "     " + str(B_court_2)

                            LCD1602.write(0, 0, str(str1))
                            LCD1602.write(0, 1, str(str2))

                            status = 1
                        else:
                            if curTimSelect == 3:
                                LCD1602.write(0, 1, "      ^         ")
                            elif curTimSelect == 2:
                                LCD1602.write(0, 1, "       ^        ")
                            elif curTimSelect == 1:
                                LCD1602.write(0, 1, "         ^      ")
                            else:
                                LCD1602.write(0, 1, "          ^     ")
                    continue

                # after show the data, you can take another round of search
                if status == 1 and but_1_state != pre_but_1:
                    break
    except KeyboardInterrupt:
        print("Close Program")
        GPIO.cleanup()
except KeyboardInterrupt:
    print("Close Program")
    GPIO.cleanup()
finally:
    LCD1602.clear()

