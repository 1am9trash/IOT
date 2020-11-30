import time
import http.client
import urllib
import json
import RPi.GPIO as GPIO
import requests
import socket


# print the POST message, to check it's status, data and update time
def printPost(payload, response):
    print("Status:       ", response.status)
    print("Data:         ", json.dumps(payload))
    print("Update time:  ", time.strftime("%c"))
    print()

# post data to MCS
def postToMCS(payload, deviceId, deviceKey):
    headers = {"Content-type": "application/json", "deviceKey": deviceKey}
    notConnected = 1

    while (notConnected):
        try:
            conn = http.client.HTTPConnection("api.mediatek.com:80")
            conn.connect()
            notConnected = 0
        except (http.client.HTTPException, socket.error) as ex:
            print ("Error: %s" % ex)
            time.sleep(10)

    conn.request("POST", "/mcs/v2/devices/" + deviceId +
                 "/datapoints", json.dumps(payload), headers)
    response = conn.getresponse()

    printPost(payload, response)
    conn.close()


def readLdr(PIN):
    reading = 0
    GPIO.setup(PIN, GPIO.OUT)
    GPIO.output(PIN, False)
    time.sleep(0.1)
    GPIO.setup(PIN, GPIO.IN)
    while (GPIO.input(PIN) == False):
        reading = reading + 1
    return reading


if __name__ == '__main__':
    # set to BOARD mode, it's easier to find the pin position
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # 4 ldr sensors' pin
    ldrPin = [35, 36, 37, 38]
    # 4 ldr sensors' Id on MCS
    dataChnId = ["A_ldr_1", "A_ldr_2", "B_ldr_1", "B_ldr_2"]

    # MCS device ID and key
    # it's not our real ID and ke
    deviceId = "no hacking"
    deviceKey = "no hacking"
    try:
        while True:
            for i in range(4):
                payLoad = {"datapoints": [
                    {"dataChnId": dataChnId[i], "values": {"value": str(ldrPin[i])}}]}
                postToMCS(payLoad, deviceId, deviceKey)
    except KeyboardInterrupt:
        print("Close Program")
