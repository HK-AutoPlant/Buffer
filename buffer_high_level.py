#!/usr/bin/env python

import serial
import time
import signal
import sys
import threading
import RPi.GPIO as GPIO
import logging
from SC import usbCommunication
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


# class NanoUsb(object):
#     """
#     This class creates base communication methods between Rpi and Arduino Nano
#     read/write methods using typical API write/recv
#     Needs more functions!
#     """
#     def __init__(self, port=""):
#         """
#         Opens Serial connection via USB from
#         """
#         baud = 115200
#         if port == "":
#             port = "/dev/ttyUSB0"
#         try:
#             self.serial_nano = serial.Serial(str(port), baudrate=baud, timeout=0.01)  # Example, can be ttyUSB0/1 etc
#         except ValueError as e:
#             pass
#         if port == "/dev/ttyUSB0":
#             self.tray_id = 1
#         elif port == "/dev/ttyUSB1":
#             self.tray_id = 2
#         else:
#             self.tray_id = 1
# 
#     def serial_waiting(self, nano):
#         """
#         Waiting Function that waits and then decodes a message
#         Waits until there's a communication waiting on the BUS
#         :return: True
#         True is only returned when there's more than 0 bytes on the serial connection to be read
#         """
#         if self.serial_nano.in_waiting > 0:
#             return True
# 
#     def write(self, two, three):
#         data = self.tray_id*100+10*two+three
#         self.serial_nano.sendMessage(data)
# 
#     def recv(self):
#         data = self.serial_nano.readline()
#         return data  # .decode('Ascii')


class EmergencyInterruptException(Exception):
    pass


class NoTrayReadyException(Exception):
    pass


class BufferControl(usbCommunication):
    """
    This class deals with overall workings and logics for the buffer system
    Call this class to create one thread for one buffer tray system(?)
    TODO Ask Mattias how to assign "workers" to a function (would be neat to use!!!)
    If both trays are ready, use tray 1
    """
    def __init__(self, arduino_port):
        super().__init__(arduino_port, 115200)
        """
        :param arduino_port:
        """

        self.sendMessage_array = 0
        self.read_array = 0
        self.tray_ready = False
        self.tray_position = 0
        self.tray_id = 1
        # 0 is initial position, 1 means tray is in position to drop plant from cup 1
        self.move_ready = False
        # When True, a tray has reached the restock zone and is in waiting state
        self.nano_return_int = 111
        self.tray_position_restock = 1
        self.restock_counter = 0
        self.plant_in_cup = [0,0,0,0,0]
        """
        Below: Old Variables
        """
        self.sensor_pin = 20
        self.GPIO = GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.sensor_pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        # Setup the thread sensor interrupts to appropriate sensor pin
        # self.GPIO.add_event_detect(self.sensor_pin, self.GPIO.BOTH,
        #                            callback=self.sensor_interrupt_callback(), bouncetime=50)
        self.logging = logging
        self.logging.basicConfig(level=logging.DEBUG, filename="thread_logger.log",
                                 filemode="w", format='%(name)s - %(levelname)s - %(message)s '
                                                      '-%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        self.logging.debug("Started high level buffer thread")
        self.move_tray_init()
        self.sendMessage("111")
        # self.sendMessage(1,1)

    def move_tray_init(self, input_var=True):
        # TODO replace with correct ints
        self.sendMessage("100")
        # function to move tray to restock position
        self.read()
        self.tray_position = 0
        # Assigns tray position variable to init position
        self.tray_ready = input_var
        # tray_ready variable is True, (for is_ready function call)

    def state_machine(self):
        """
        Buffer State Machine
        Calls a function for each state
        :return:
        """
        if self.tray_ready:
            counter = 0
            self.check_plants()
            for i in range(len(self.plant_in_cup)):
                if self.plant_in_cup[i] == 1:
                    counter = counter + 1
            if counter == 5:
                state = 1
                self.logging.debug("5 Plants were found after restock")
            elif counter == 0:
                state = 20
                self.logging.error("No plants were found after restock. Tray will perform reset")
            else:
                state = 1
                self.logging.warning("5 Plants were not found after restock, "
                                     "%d Plants were found in tray" % counter)
            if state == 2:
                self.move_tray_state_one()
                self.tray_position = self.check_position()
                # if (self.tray_position < 800) and (self.tray_position > 700) and (self.plant_in_cup[0] == 1):
                self.open_tray()
                self.tray_position = self.check_position()

            if state == 4:
                self.move_tray_state_two()
                self.open_tray()
                # self.tray_position = self.check_position()
                # if (self.tray_position < 600) and (self.tray_position > 500):
                self.check_plants()
                while self.plant_in_cup[1] == 1:
                    self.check_plants()
                    if self.plant_in_cup[1] == 0:
                        state = 5
                    elif self.plant_in_cup[1] == 1:
                        self.open_tray()
                else:
                    # TODO Write to arduino to move to position
                    pass
            if state == 5:
                self.move_tray_state_three()
                self.open_tray()
                self.tray_position = self.check_position()
                # if (self.tray_position < 500) and (self.tray_position > 400):
                self.check_plants()
                while self.plant_in_cup[2] == 1:
                    self.check_plants()
                    if self.plant_in_cup[2] == 0:
                        state = 6
                    elif self.plant_in_cup[2] == 1:
                        self.open_tray()
                else:
                    # TODO Write to arduino to move to position 3
                    pass
            if state == 6:
                self.move_tray_state_four()
                self.open_tray()
                self.tray_position = self.check_position()
                # if (self.tray_position < 400) and (self.tray_position > 300):
                self.check_plants()
                while self.plant_in_cup[3] == 1:
                    self.check_plants()
                    if self.plant_in_cup[3] == 0:
                        state = 7
                    elif self.plant_in_cup[3] == 1:
                        self.open_tray()
                else:
                    # TODO Write to arduino to move to position 4
                    pass
            if state == 7:
                self.move_tray_state_five()
                self.open_tray()
                self.tray_position = self.check_position()
                # if (self.tray_position < 300) and (self.tray_position > 200):
                self.check_plants()
                while self.plant_in_cup[4] == 1:
                    self.check_plants()
                    if self.plant_in_cup[4] == 0:
                        state = 8
                    elif self.plant_in_cup[4] == 1:
                        self.open_tray()
                else:
                    # TODO Write to arduino to move to position 5
                    pass
            if state == 8:
                self.move_tray_to_end()
            if state == 20:
                self.move_tray_init()

    def check_plants(self):
        """Writes 06 to arduino
        Reads out header + 5 digits
        If message header is 6, stores plant in cup as 1 (in cup) | 0 (not in cup)
        :return: array 5 spots
        """
        self.sendMessage("106")
        output_array = []
        data = self.read()
        for i in range(len(data)):
            output_array.append(data)
        if output_array[0] == 6:
            output_array = output_array[1:]
        return output_array

    def check_position(self):
        self.sendMessage(107)
        output_array = []
        data = self.readMessage()
        for i in range(len(data)):
            output_array.append(data)
        if output_array[0] == 6:
            output_array = output_array[1:]
        return output_array

    def move_tray_to_end(self):
        self.move_tray_init(False)

    def open_tray(self):
        #self.sendMessage(1,2,3)
        #
        self.logging.debug("There is no motor for this finished")

    def move_tray_state_one(self):
        """
        Moves a tray to first drop off position one
        :return: 
        """
        self.sendMessage("111")
        waiting_for_finish = True
        while waiting_for_finish:
            waiting_for_finish = self.read()

    def move_tray_state_two(self):
        """
        Moves a tray to first drop off position one
        :return: 
        """
        self.sendMessage("112")
        waiting_for_finish = True
        while waiting_for_finish:
            waiting_for_finish = self.read()

    def move_tray_state_three(self):
        """
        Moves a tray to first drop off position one
        :return: 
        """
        self.sendMessage("112")
        waiting_for_finish = True
        while waiting_for_finish:
            waiting_for_finish = self.read()

    def move_tray_state_four(self):
        """
        Moves a tray to first drop off position one
        :return: 
        """
        self.sendMessage("114")
        waiting_for_finish = True
        while waiting_for_finish:
            waiting_for_finish = self.readMessage()

    def move_tray_state_five(self):
        """
        Moves a tray to first drop off position one
        :return: 
        """
        self.sendMessage("115")
        waiting_for_finish = True
        while waiting_for_finish:
            waiting_for_finish = self.readMessage()

    def move_tray_to_start(self):
        self.sendMessage("110")

    def start_tray_two(self):
        # This Function should move tray two from drop-off zone and back
        pass

    def read(self):
        while True:
            read = self.readMessage()
            time.sleep(0.1)
            if read == self.nano_return_int:
                break
        return read

    def trees_dropped(self, tray_number=None):
        self.tray_ready = False

    def is_ready(self):
        """
        Callable function that will tell you if a tray is ready or not,
        :return: True | False & None
        The function returns true if a tray is ready to receive plants
        and an int (1 or 2) that corresponds to the position of the tray.
        When False a None type object is the second return parameter.
        """
        return self.tray_ready, self.tray_position_restock

    def sensor_interrupt_callback(self):
        print("Sensor Triggered")
    #
    #     # TODO After performing system reset, send a wait to gripper/gantry
    #     # TODO After an entire rerun of the tray has been performed, stop wait
    #     raise EmergencyInterruptException()


if __name__ == '__main__':
    Buffer_Control = BufferControl("/dev/ttyACM0")
    # Start state machine
    Buffer_Control.state_machine()
