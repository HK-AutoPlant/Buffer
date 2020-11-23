from SC import usbCommunication
import time

class randomnameClass():
    def __init__(self, arduino_port="/dev/ttyUSB0"):
        self.comm = usbCommunication(arduino_port, 115200)
        
    def test_message(self):
        msg = "123" # input("Input message: ")
        self.comm.sendMessage(str(msg.rstrip()))
        print("something is sent")
        time.sleep(1)
        print("Message return: %s" % self.comm.readMessage())

if __name__ == "__main__":
    testing = randomnameClass()
    time.sleep(1)
    testing.test_message()
