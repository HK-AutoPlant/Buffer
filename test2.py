from SC import usbCommunication
import time

class randomnameClass():
    def __init__(self, arduino_port="/dev/ttyUSB0"):
        self.comm = usbCommunication(arduino_port, 115200)
        
    def test_message(self):
        msg = input("Input message: ")
        self.comm.sendMessage(msg)
        print("something is sent")
        time.sleep(0.5)
        print("Message return: %s" % self.comm.readMessage())

if __name__ == "__main__":
    testing = randomnameClass()
    testing.test_message()
