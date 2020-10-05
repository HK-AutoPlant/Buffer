#!/usr/bin/env python

import serial
import time
import signal
import sys
import threading
import RPi.GPIO as GPIO

"""
HK2020 Autoplant 1 - Buffer Subsystem
This is the high level software main file for the 2020 Mechatronics HK - Autoplant 1
This file controls the high level logic for the buffer system.
Run this file to control the low level
Microcontrollers (Arduino Nanos) which in turn control the hardware.
This file has following classes:
MainBuffer
NanoUsb(port(optional, preset to /dev/ttyUSB0), baud(optional, preset to 115200)
"""

class EmergencyInterruptException(Exception):
    print("Emergency Sensor Triggered")
    pass

class BufferThread(threading.Thread):
    """
    This class deals with overall workings and logics for the buffer system
    Call this class to create one thread for one buffer tray system
    Sends the "init" string to Arduino tied to thread
    Arduino handling
    """
    def __init__(self, arduino_port, thread_id, thread_counter):
        """

        :param arduino_port: Insert the
        """
        # Init thread params, open connection to arduino tied to this thread
        threading.Thread.__init__(self)
        self.Nano = NanoUsb(arduino_port)
        self.thread_id = thread_id
        self.thread_counter = thread_counter
        self.listen = self.Nano.recv()
        self.sensor_pin = 20
        self.GPIO = GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.sensor_pin,self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.GPIO.add_event_detect(self.sensor_pin, self.GPIO.FALLING,
                                   callback=self.sensor_interrupt_callback(), bouncetime=50)
        # Decide callback function (handles interrupt)
        # If several sensor messages within 50ms, ignore (due to the "lag" of reality)

        # When connected to arduino, move tray to init position
        self.Nano.write("init")
        state = False
        while state:
            # Waits until Arduino returns complete string
            self.listen = self.Nano.recv()
            if state is False:
                self.listen = self.Nano.recv()
                time.sleep(0.1)
                if self.listen == "complete_init":
                    state = True

    def signal_handler(self, sig, frame):
        GPIO.cleanup()
        sys.exit(0)

    def sensor_interrupt_callback(self):
        # TODO Do Some Interrupt Code Here
        raise EmergencyInterruptException()

    def run(self):
        """
        Main thread loop function
        :return:
        """
        while True:
            self.listen = self.Nano.recv()
            # Some Way To Get Buffer Comm That Plants Handed Off
            self.Nano.write("function_1")
            # Tell Arduino to execute function 1
            self.listen = self.Nano.recv()
            state = False
            # Waits for function 1 to be finished
            while state is False:
                if self.listen == "complete_1":
                    state = True
                time.sleep(0.1)
                self.listen = self.Nano.recv()


class NanoUsb:
    """
    This class creates base communication methods between Rpi and Arduino Nano
    read/write methods using typical API write/recv
    Needs more functions!
    """
    def __init__(self, port=None, baud=115200):
        """
        Opens Serial connection via USB from
        """
        if port is None:
            port = "/dev/ttyUSB0"
        try:
            self.serial_nano = serial.Serial(str(port), baud)  # Example, can be ttyUSB0/1 etc
        except(ValueError, self.serial_nano.SerialException) as e:
            print(e)

    def serial_waiting(self, nano):
        """
        Waiting Function that waits and then decodes a message
        Waits until there's a communication waiting on the BUS
        :return: True
        True is only returned when there's more than 0 bytes on the serial connection to be read
        """
        if self.serial_nano.in_waiting > 0:
            return True

    def write(self, data):
        self.serial_nano.write(data)

    def recv(self):
        data = self.serial_nano.readline()
        return data.decode('Ascii')

if __name__ == '__main__':
    thread_one = BufferThread("/dev/ttyUSB0", "upper tray", 1)
    thread_one.start()
