# A sketch to test the serial communication with the Arduino.

import serial
import time

#'/dev/ttyACM0'
# -- Commands --
#   z100    Moves the carriage down 100 mm
#   z-100   Moves the carriage up 100 mm
#   Home    Moves the carriage to the home position

class usbCommunication():
    def __init__(self, port, baudRate):
        port = '/dev/ttyACM0'
        baudRate = 115200
        print(baudRate)
        self.message = None
        try:
            self.ser = serial.Serial(port, baudRate, timeout=1)
        except serial.portNotOpenError as e:
            print(e)

	#Input: #z100 for z 100mm down. z-100 for 100mm up
	# Homing: send "home"
    def sendMessage(self, msg):
        self.ser.write(msg.encode('utf-8')) 

	#Output: Confirms whats has been sent
	# if input NOT understood it reports that aswell
    def readMessage(self):
        self.message = self.ser.readline().decode('utf-8').rstrip()
        print(self.message)
        return self.message

    def messageRecieved(self):
        if(self.ser.in_waiting > 0):
            return True
        else:
            return False
if __name__ == "__main__":
    zAxisUsbPort = '/dev/ttyACM0'

    test = usbCommunication(zAxisUsbPort, 115200)

    while(True):
        msg = input("Input Command: ")
        test.sendMessage(msg)
        time.sleep(0.5)
        # while(test.messageRecieved() is True):
        test.readMessage()