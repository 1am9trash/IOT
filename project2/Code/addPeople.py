import RPi.GPIO as GPIO
import time
import requests
import http.client
import urllib
import json
import socket


def printPost(payload, response):
    print("Status:       ", response.status)
    print("Data:         ", json.dumps(payload))
    print("Update time:  ", time.strftime("%c"))
    print()


def getNumberOfPeople(deviceId, deviceKey):
    url = "http://api.mediatek.com/mcs/v2/devices/" + \
        deviceId + "/datachannels/Number_of_people/datapoints"
    headers = {"Content-type": "application/json", "deviceKey": deviceKey}
    r = requests.get(url, headers=headers)
    value = (r.json()["dataChannels"][0]["dataPoints"][0]["values"]["value"])
    return value


def postNumberOfPeople(payload, deviceId, deviceKey):
    url = "https://api.mediatek.com/mcs/v2/devices/" + deviceId + "/datapoints"
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


if __name__ == '__main__':

    MONITOR_PIN = 26
    LED_PIN = 11
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(MONITOR_PIN, GPIO.IN)
    GPIO.setup(LED_PIN, GPIO.OUT)

    # not real Id and Key
    deviceId = "no hacking"
    deviceKey = "no hacking"

    try:
        while True:
            GPIO.output(LED_PIN, GPIO.LOW)
            while GPIO.input(MONITOR_PIN):
                GPIO.output(LED_PIN, GPIO.HIGH)
                num = getNumberOfPeople(deviceId, deviceKey)
                payLoad = {"datapoints": [
                    {"dataChnId": "Number_of_people", "values": {"value": str(num + 1)}}]}
                postNumberOfPeople(payLoad, deviceId, deviceKey)
                time.sleep(8)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Close Program")
