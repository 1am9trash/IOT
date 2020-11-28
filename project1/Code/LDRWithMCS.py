import time
import http.client
import urllib
import json
import RPi.GPIO as GPIO
import requests
import socket

# set to BOARD mode, it's easier to find the pin position
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

A_ldr_1 = 35
A_ldr_2 = 36
B_ldr_1 = 37
B_ldr_2 = 38

# MCS device ID and key
# it's not our real ID and key
deviceId = "no hacking"
deviceKey = "no hacking"

# post data to MCS
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
        conn.request("POST", "/mcs/v2/devices/" + deviceId + "/datapoints", json.dumps(payload), headers)
        response = conn.getresponse()

        # print the POST message, to check it's status, data and time
        print("Status:       ", response.status)
        print("Data:         ", json.dumps(payload))
        print("Update time:  ", time.strftime("%c"))
        print()

        data = response.read()
        conn.close()

def read_ldr(PIN):
    reading = 0
    GPIO.setup(PIN, GPIO.OUT)
    GPIO.output(PIN, False)
    time.sleep(0.1)
    GPIO.setup(PIN, GPIO.IN)
    while (GPIO.input(PIN) == False):
        reading = reading + 1
    return reading

try:
    while True:
        # in our simulated court, there are 4 slots
        A_ldr_1_reading = read_ldr(A_ldr_1)
        A_ldr_2_reading = read_ldr(A_ldr_2)
        B_ldr_1_reading = read_ldr(B_ldr_1)
        B_ldr_2_reading = read_ldr(B_ldr_2)

        # use function to post data
        A_1_payload = {"datapoints": [{"dataChnId": "A_ldr_1", "values": {"value": str(A_ldr_1_reading)}}]}
        post_to_mcs(A_1_payload)
        A_2_payload = {"datapoints": [{"dataChnId": "A_ldr_2", "values": {"value": str(A_ldr_2_reading)}}]}
        post_to_mcs(A_2_payload)
        B_1_payload = {"datapoints": [{"dataChnId": "B_ldr_1", "values": {"value": str(B_ldr_1_reading)}}]}
        post_to_mcs(B_1_payload)
        B_2_payload = {"datapoints": [{"dataChnId": "B_ldr_2", "values": {"value": str(B_ldr_2_reading)}}]}
        post_to_mcs(B_2_payload)
except KeyboardInterrupt:
    print("Close Program")

    


