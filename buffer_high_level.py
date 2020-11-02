#!/usr/bin/env python

import serial
import time
import signal
import sys
import threading
import RPi.GPIO as GPIO
import logging
"""
HK2020 Autoplant 1 - Buffer Subsystem
This is the high level software main file for the 2020 Mechatronics HK - Autoplant 1
This file controls the high level logic for the buffer system.
Run this file to control the low level
Microcontrollers (Arduino Nanos) which in turn control the hardware.
This file has following classes:
MainBuffer
NanoUsb(port(optional, preset to /dev/ttyUSB0), baud(optional, preset to 115200)
https://roboticsbackend.com/raspberry-pi-gpio-interrupts-tutorial/
"""


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

    def write(self, one, two, three, four):
        data = one+two+three+four
        self.serial_nano.write(data)

    def recv(self):
        data = self.serial_nano.readline()
        return data     #.decode('Ascii')


class EmergencyInterruptException(Exception):
    print("Emergency Sensor Triggered")
    pass

class NoTrayReadyException(Exception):
    pass

class BufferControl(NanoUsb):
    """
    This class deals with overall workings and logics for the buffer system
    Call this class to create one thread for one buffer tray system(?)
    TODO Ask Mattias how to assign "workers" to a function (would be neat to use!!!)
    If both trays are ready, use tray 1
    """
    def __init__(self, arduino_port):
        super().__init__(arduino_port)
        """
        :param arduino_port:
        """

        self.write_array = 0
        self.read_array = 0
        self.tray_ready = False
        self.tray_ready_position = None
        self.move_tray_init()
        self.move_ready = False
        # When True the tray is ready to be moved from drop-off
        """
        Below: Old Variables
        """
        self.sensor_pin = 20
        self.GPIO = GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.sensor_pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        # Setup the thread sensor interrupts to appropriate sensor pin
        self.GPIO.add_event_detect(self.sensor_pin, self.GPIO.BOTH,
                                   callback=self.sensor_interrupt_callback(), bouncetime=50)
        self.logging = logging
        self.logging.basicConfig(level=logging.DEBUG, filename="thread_logger.log",
                                 filemode="w", format='%(name)s - %(levelname)s - %(message)s '
                                                      '-%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        self.logging.debug("Started high level buffer thread")def __init__(self, arduino_port):
        super().__init__(arduino_port)
        """
        :param arduino_port:
        """

        self.write_array = 0
        self.read_array = 0
        self.tray_ready = False
        self.tray_ready_position = None
        self.move_tray_init()
        self.move_ready = False
        # When True the tray is ready to be moved from drop-off
        """
        Below: Old Variables
        """
        self.sensor_pin = 20
        self.GPIO = GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.sensor_pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        # Setup the thread sensor interrupts to appropriate sensor pin
        self.GPIO.add_event_detect(self.sensor_pin, self.GPIO.BOTH,
                                   callback=self.sensor_interrupt_callback(), bouncetime=50)
        self.logging = logging
        self.logging.basicConfig(level=logging.DEBUG, filename="thread_logger.log",
                                 filemode="w", format='%(name)s - %(levelname)s - %(message)s '
                                                      '-%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        self.logging.debug("Started high level buffer thread")

    def move_tray_init(self):
        # TODO replace with correct ints
        self.write(1, 1, 0, 0)
        read_array = self.read()
        self.tray_ready_position = read_array[0]
        self.tray_ready = True

    def move_ready_tray(self):
        while True:
            while not self.tray_ready:
                if self.tray_ready_ready:
                    # Move the tray that's from buffer
                    if self.tray_ready_position == 1:
                        self.start_tray_one()
                    elif self.tray_ready_position == 2:
                        self.start_tray_two
                    else:
                        raise NoTrayReadyException
                time.sleep(0.25)

    def start_tray_one(self):
        # This Function should move tray one from drop-off zone and back
        # Moves tray to end of the rail
        # Moves tray from end to position 1
        # Iterates the tray one plant drop position at a tie
        # Add functions for sending open command to the servos in between (1,2,3,4,5)
        self.move_tray_to_end()
        if self.read() == 1234:
            pass
        self.move_tray_to_drop_start()
        if self.read() == 1234:
            self.move_tray_one_step(1)
            if self.read() == 1234:
                self.move_tray_one_step(2)
                if self.read() == 1234:
                    self.move_tray_one_step(3)
                    if self.read() == 1234:
                        self.move_tray_one_step(4)
                        if self.read() == 1234:
                            self.move_tray_one_step(5)
                            if self.read() == 1234:
                                self.move_tray_to_start()
        pass

    def start_tray_two(self):
        # This Function should move tray two from drop-off zone and back
        pass

    def read(self):
        self.read_array = self.recv()
        read_array_old = self.read_array
        return_array = []
        while read_array_old == self.read_array:
            self.read_array = self.recv()
            if self.read_array == read_array_old:
                time.sleep(0.05)
            for i in self.read_array:
                return_array.append(i)
            return return_array

    def trees_dropped(self, tray_number):
        self.tray_ready_position = tray_number
        self.move_ready = True

    def is_ready(self):
        """
        Callable function that will tell you if a tray is ready or not,
        :return: True | False & None
        The function returns true if a tray is ready to receive plants
        and an int (1 or 2) that corresponds to the position of the tray.
        When False a None type object is the second return parameter.
        """
        tray_ready = self.tray_ready
        tray_position = self.tray_ready_position
        if tray_ready is False:
            tray_position = None
        return tray_ready, tray_position

    # def signal_handler(self, sig, frame):
    #     GPIO.cleanup()
    #     sys.exit(0)
    #
    def sensor_interrupt_callback(self):
        print("Sensor Triggered")
    #
    #     # TODO After performing system reset, send a wait to gripper/gantry
    #     # TODO After an entire rerun of the tray has been performed, stop wait
    #     raise EmergencyInterruptException()
    #
    # def run(self):
    #     """
    #     Main thread loop function
    #     :return:
    #     """
    #     while True:
    #         self.listen = self.Nano.recv()
    #         # Some Way To Get Gripper That Plants Handed Off
    #         self.Nano.write("function_1")
    #         # Tell Arduino to execute function 1
    #         self.listen = self.Nano.recv()
    #         state = False
    #         # Waits for function 1 to be finished
    #         while state is False:
    #             if self.listen == "complete_1":
    #                 state = True
    #             time.sleep(0.1)
    #             self.listen = self.Nano.recv()
    #


class tray1():
    def __init__(self, arduino_port):
        super().__init__(arduino_port)
        
        self.no_of_cups = 5
        self.plant_detect = [1,2,3,4,5] #Should contain the number of cup's which are full.
        self.detect_position = 0 #should contain distance in mm from home
        self.current_position = Home
        """
        :param arduino_port:
        """

        self.write_array = 0
        self.read_array = 0
        self.tray_ready = False
        self.tray_ready_position = None
        self.move_tray_init()
        self.move_ready = False

    def tray_posedetection(self):
        arduino keeps track of where tray is with respect to home
        if self.detect_position <= 10:
            self.current_position = Home
        elif self.detect_position >= 150 and self.detect_position <= 200:
            self.current_position = First_Dropoff
        elif self.detect_position > 200 and self.detect_position <= 250:
            self.current_position = Second_Dropoff
        elif self.detect_position > 250 and self.detect_position <= 300:
            self.current_position = Third_Dropoff
        elif self.detect_position > 300 and self.detect_position <= 350:
            self.current_position = Fourth_Dropoff
        elif self.detect_position > 350 and self.detect_position <= 400:
            self.current_position = Fifth_Dropoff
        elif self.detect_position > 500 and self.detect_position <= 800:
            self.current_position = Restock
        """ Add more postiions if in mind """
        
    def Homing_Seq(self):
        #Everytime system is restarted and switched from manual back to auto and position at home
        #perform Homing
        elif restock_count == 20:
            self.output_array = append[]

    def Restocking_Seq(self):
        #When all the cups are empty and tray position near to home
        if self.plant_detect is None and self.detect_position == Home:
            self.output_array = append[] #perform restocking i.e write the number to output array
        
    
    def dropoff_seq(self):
        when all the cups are full and tray position near dropoff
        if self.plant_detect is full and self.detect_position == 
        x = 1
        for x:5
            dropoff(1)
            if dropoff(1) success:
                dropoff(x+1)
            else:
                print('Waiting Dropoff x')

    def dropoff_seq(self,cup_no):
        if cup_no sensor high: #Check the cup for the presence of Plant
            write the number to output array for movement.
        else:
            return('Cup number this .. is empty')

    


    








if __name__ == '__main__':
    Buffer_Control = BufferControl("/dev/ttyUSB0")
