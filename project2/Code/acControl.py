import os
import Adafruit_DHT
import RPi.GPIO as GPIO

if __name__ == '__main__':
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 22
    isOn = False

    try:
        while True:
            humidity, temperature = Adafruit_DHT.read_retry(
                DHT_SENSOR, DHT_PIN)
            if temperature >= 28 and isOn == False:
                os.system('irsend SEND_ONCE AC KEY_POWER')
                isOn = True
            if temperature <= 24 and isOn == True:
                os.system('irsend SEND_ONCE AC KEY_POWER')
                isOn = False
    except KeyboardInterrupt:
        print("Close Program")
