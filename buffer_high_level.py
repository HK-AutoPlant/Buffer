#!/usr/bin/env python

import serial
import time
import RPi.GPIO as GPIO
import logging
from SC import usbCommunication
from termcolor import colored
"""
HK2020 Autoplant 1 - Buffer Subsystem
This is the high level software main file for the 2020 Mechatronics HK - Autoplant 1
This file controls the high level logic for the buffer system.
Run this file to control the low level
Microcontrollers (Arduino Nanos) which in turn control the hardware.
This file has following classes:
MainBuffer
Imports usbCommunication from Autoplant/Gantry (Credit: Philip)
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


class BufferControl():
    """
    This class deals with overall workings and logics for the buffer system
    Call this class to create one thread for one buffer tray system(?)
    TODO Ask Mattias how to assign "workers" to a function (would be neat to use!!!)
    If both trays are ready, use tray 1
    """
    def __init__(self, arduino_port="/dev/ttyACM0"):
        # super().__init__(arduino_port, 115200)
        """
        :param arduino_port: port ID for the arduino device
        :type arduino_port: String 
        """
        baudRate = 9600
        self.message = None
        self.ser = serial.Serial(arduino_port, baudRate, timeout=1)
        print(self.ser.name)
        com_open =  self.ser.is_open
        if com_open:
            print("--------------------------------------------------------\n")
            print(colored("COM PORT is open, please wait", 'green'))
            for i in range(5):
                time.sleep(1)
                print(colored("Time left: " + str(9 - i), 'green'))
            print(colored("Tray setup is ready!", "green"))
            print("--------------------------------------------------------")
        elif not com_open:
            print("--------------------------------------------------------\n")
            print(colored("COM PORT is not open, please check error logs in terminal", 'red'))
            print("--------------------------------------------------------")   
        #time.sleep(10)
        #print("sleep over")
        self.tray_ready = False
        self.tray_ready_id = 1
        self.state = 0
        self.state_machine_counter = 0
        # 0 is initial position, stores position as states
        self.move_ready = False
        # When True, a tray has reached the restock zone and is in waiting state
        self.restock_counter = 0
        self.plant_in_cup = [0,0,0,0,0]
        # self.sensor_pin = 20
        # self.GPIO = GPIO
        # self.GPIO.setmode(self.GPIO.BCM)
        # self.GPIO.setup(self.sensor_pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        # Setup the thread sensor interrupts to appropriate sensor pin
        # self.GPIO.add_event_detect(self.sensor_pin, self.GPIO.BOTH,
        #                            callback=self.sensor_interrupt_callback(), bouncetime=50)
        self.logging = logging
        self.logging.basicConfig(level=logging.DEBUG, filename="thread_logger.log",
                                 filemode="w", format='%(name)s - %(levelname)s - %(message)s '
                                                      '-%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        self.logging.debug("Started high level buffer thread")
        self.move_tray_init()

    def sendMessage(self, msg):
        self.ser.reset_input_buffer()
        self.ser.write(msg.encode('utf-8'))
        time.sleep(0.5)
        
    def readMessage(self):
        # self.ser.reset_output_buffer()
        if self.messageRecieved():
            message = self.ser.readline().decode('utf-8').rstrip()
            self.ser.reset_output_buffer()
            print("Message Read: %s" % message)
            return message
        else:
            pass

    def messageRecieved(self):
        if(self.ser.in_waiting > 0):
            return True
        else:
            return False

    #######
    # API #
    #######

    def is_tray_ready(self):
        """Outwards API, call this to check if a tray is ready
        If a tray is ready, return True and which tray 
        Note: Defaults to 1 if both trays are ready

        Returns:
            [boolean]: [True = Yes | False = No]
            [int]: [tray id for tray 1 or 2]
            
        """
        return self.tray_ready, self.tray_ready_id

    def start_tray(self):
        """Outwards API, when trees have been deposited, call this to start
        state machine
        """
        self.state_machine_runner()
    
    def tray_is_ready(self, tray_id):
        """[Use this function at the end of state machine
        Notifies the UI that a tray is ready and takes its tray ID
        # TODO get an API from Mathis/other that can be called for this action
        # ]

        Args:
            tray_id ([int]): [tray ID of the ready tray]

        Raises:
            EmergencyInterruptException: [Something went horribly wrong]

        Returns:
            [boolean]: [Did we succeed or not? Might need a return]
        """
        self.logging.info("Get a callable API to update UI that a tray is ready")
        # return True

    ##############################
    # Tray control functionality #
    ##############################
    
    def move_tray_init(self, tray_num=1, input_var=True):
        """[Function to perform homing, or move tray to initial
        position]

        Args:
            input_var (bool, optional): [description]. Defaults to True.
        """
        msg = "1000000"
        self.sendMessage(msg)
        self.tray_position = 0
        # Assigns tray position variable to init position
        self.tray_ready = input_var
        self.tray_ready_id = tray_num
        # self.ser.reset_input_buffer()
        # time.sleep(5)
        # self.sendMessage("8000001")
        # tray_ready variable is True, (for is_ready function call)
        waiting_for_finish = self.messageRecieved()
        while not waiting_for_finish:
            return_data = self.readMessage()
            waiting_for_finish = self.messageRecieved()
            if return_data == "999" or return_data == "999":
                waiting_for_finish = True
            elif return_data == "666" or return_data == "666":
                waiting_for_finish = True
                # raise NoTrayReadyException
            else:
                pass
            time.sleep(0.5)
        self.tray_ready = True
    
    def state_machine_runner(self):
        if self.state_machine_counter % 2 == 1:
            self.state_machine()
        else:
            self.state_machine_two()
        self.state_machine_counter += 1
    
    def state_machine_two(self):
        """[State machine from left to right side]
        """
        self.ser.reset_input_buffer()
        self.move_tray_to_restock()
        time.sleep(10)
        print(colored("Restock","green"))
        self.move_tray_state_five()
        time.sleep(1)
        self.open_tray()
        time.sleep(0.5)
        self.move_tray_state_four()
        time.sleep(1)
        self.open_tray()
        time.sleep(0.5)
        self.move_tray_state_three()
        time.sleep(1)
        self.open_tray()
        time.sleep(0.5)
        self.move_tray_state_two()
        time.sleep(1)
        self.open_tray()
        time.sleep(0.5)
        self.move_tray_state_one()
        time.sleep(1)
        self.open_tray()
        time.sleep(0.5)
        self.state_machine_counter = self.state_machine_counter + 1
        self.tray_ready = True

    def state_machine(self):
        """[State machine from right to left side]
        """
        self.ser.reset_input_buffer()
        self.move_tray_state_one()
        time.sleep(1)
        print("check 1")
        self.open_tray()
        print("open tray")
        time.sleep(0.5)
        self.move_tray_state_two()
        time.sleep(1)
        self.open_tray(2)
        print("open tray")
        time.sleep(0.5)
        print("check 2")
        self.move_tray_state_three()
        time.sleep(1)
        print("check 3")
        self.open_tray()
        print("open tray")
        time.sleep(0.5)
        self.move_tray_state_four()
        time.sleep(1)
        print("check 4")
        self.open_tray(2)
        print("open tray")
        self.move_tray_state_five()
        time.sleep(1)
        print("check 5")
        self.open_tray()
        print("open tray")
        self.move_tray_to_restock()
        time.sleep(10)
        self.state_machine_counter = self.state_machine_counter + 1
        self.tray_ready = True
                    
    def current_state(self):
        """[Call this function to check the current state and position of the tray]

        Returns:
            [int, float]: [the state and the position in mm]
        """
        self.sendMessage("103")
        return_data = []
        return_data = self.readMessage()
        data_formated = return_data[2:]
        data = float(data_formated)
        self.tray_position = data
        if self.tray_position < 0 and self.tray_position < 123:
            self.state = 1
        elif self.tray_position < 0 and self.tray_position < 123:
            self.state = 2
        elif self.tray_position < 0 and self.tray_position < 123:
            self.state = 3
        elif self.tray_position < 0 and self.tray_position < 123:
            self.state = 4
        elif self.tray_position < 0 and self.tray_position < 123:
            self.state = 5
        elif self.tray_position < 0 and self.tray_position < 123:
            self.state = 6
        else:
            self.state = 8
            self.logging.error = ("No tray position withint boundaries, tray position returned as %s" 
                                  % self.tray_position)
        return self.state, self.tray_position

    def check_plants(self):
        """[This function query sensor data from arduino for the plants if in cup]

        Returns:
            [Array]: [An array of length 5 with 0 or 1 for no plant or a plant]
        """
        self.sendMessage("6000000")
        output_array = []
        data = self.readMessage()
        for i in range(len(data)):
            output_array.append(data)
        if output_array[0] == 6:
            output_array = output_array[1:]
        return output_array

    def check_position(self):
        """[Checks the position of the tray in mm]

        Returns:
            [int]: [lenght [mm]]
        """
        self.sendMessage("7000000")
        output_array = []
        data = self.readMessage()
        for i in range(len(data)):
            output_array.append(data)
        if output_array[0] == 6:
            output_array = output_array[1:]
        return output_array

    def open_tray(self):
        """[This functions opens the cup]

        Args:
            direction ([String | Int]): [Identifier necessary for knowing which direction to open]
        """
        #TODO Add code when motor installed? 

        self.sendMessage("1800001")
        time.sleep(2)
        self.sendMessage("1800000")
        
            # since its even, move to open tray two
        # if (direction % 2 ) == 1:
        #     self.sendMessage("1800001")
            # since its odd, move to open tray one
        waiting_for_finish = self.messageRecieved()
        while not waiting_for_finish:
            return_data = self.readMessage()
            waiting_for_finish = self.messageRecieved()
            if return_data == "999" or return_data == "999":
                waiting_for_finish = True
            elif return_data == "666" or return_data == "666":
                waiting_for_finish = True
                # raise NoTrayReadyException
            else:
                pass
            time.sleep(0.5)   

    def move_tray_state_one(self):
        """[Move tray to state one]
        """
        self.sendMessage("1110000")
        self.ser.reset_input_buffer()
        waiting_for_finish = self.messageRecieved()
        while not waiting_for_finish:
            return_data = self.readMessage()
            waiting_for_finish = self.messageRecieved()
            if return_data == "999" or return_data == "999":
                waiting_for_finish = True
            elif return_data == "666" or return_data == "666":
                waiting_for_finish = True
                # raise NoTrayReadyException
            else:
                pass
            time.sleep(0.5)
                

    def move_tray_state_two(self):
        """[Move tray to state two]
        """
        self.sendMessage("1120000")
        self.ser.reset_input_buffer()
        waiting_for_finish = self.messageRecieved()
        while not waiting_for_finish:
            return_data = self.readMessage()
            waiting_for_finish = self.messageRecieved()
            if return_data == "999" or return_data == "999":
                waiting_for_finish = True
            elif return_data == "666" or return_data == "666":
                waiting_for_finish = True
                # raise NoTrayReadyException
            else:
                pass
            time.sleep(0.5)

    def move_tray_state_three(self):
        """[Move tray to state three]
        """
        self.sendMessage("1130000")
        self.ser.reset_input_buffer()
        waiting_for_finish = self.messageRecieved()
        while not waiting_for_finish:
            return_data = self.readMessage()
            waiting_for_finish = self.messageRecieved()
            if return_data == "999" or return_data == "999":
                waiting_for_finish = True
            elif return_data == "666" or return_data == "666":
                waiting_for_finish = True
                # raise NoTrayReadyException
            else:
                pass
            time.sleep(0.5)

    def move_tray_state_four(self):
        """[Move tray to state four]
        """
        self.sendMessage("1140000")
        self.ser.reset_input_buffer()
        waiting_for_finish = self.messageRecieved()
        while not waiting_for_finish:
            return_data = self.readMessage()
            waiting_for_finish = self.messageRecieved()
            if return_data == "999" or return_data == "999":
                waiting_for_finish = True
            elif return_data == "666" or return_data == "666":
                waiting_for_finish = True
                # raise NoTrayReadyException
            else:
                pass
            time.sleep(0.5)

    def move_tray_state_five(self):
        """[Move tray to state five]
        """
        self.sendMessage("1150000")
        self.ser.reset_input_buffer()
        waiting_for_finish = self.messageRecieved()
        while not waiting_for_finish:
            return_data = self.readMessage()
            waiting_for_finish = self.messageRecieved()
            if return_data == "999" or return_data == "999":
                waiting_for_finish = True
            elif return_data == "666" or return_data == "666":
                waiting_for_finish = True
                # raise NoTrayReadyException
            else:
                pass
            time.sleep(0.5)
            
    def move_tray_to_restock(self):
        """[Move tray to restock position]
        """
        self.sendMessage("1160000")
        self.ser.reset_input_buffer()
        waiting_for_finish = True
        while waiting_for_finish:
            return_data = self.readMessage()
            if return_data == "999" or return_data == "999":
                waiting_for_finish = False
            elif return_data == "666" or return_data == "666":
                pass
                # raise NoTrayReadyException
            else:
                pass
            time.sleep(0.1)
    
    def start_tray_two(self):
        # This Function should move tray two from drop-off zone and back
        pass

    def sensor_interrupt_callback(self):
        """[This function can be called for performing interrupt sequence]
        """
        print("Sensor Triggered")
        # TODO After performing system reset, send a wait to gripper/gantry
        # TODO After an entire rerun of the tray has been performed, stop wait
        raise EmergencyInterruptException()



if __name__ == '__main__':
    try:
        Buffer_Control = BufferControl("/dev/ttyACM0")
        Buffer_Control.state_machine_runner()
        Buffer_Control.state_machine_runner()
    except KeyboardInterrupt:
        print(colored("User Interrupt", "green"))
    except:
        pass
