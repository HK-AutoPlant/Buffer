#!/usr/bin/env python

import serial
import time
import logging
import sys
from SC import usbCommunication
from termcolor import colored
# sys.path.append("..zAxi/Python")
# from Python import usbCommunication
"""
HK2020 Autoplant 1 - Buffer Subsystem
This is the high level software main file for the 2020 Mechatronics HK - Autoplant 1
This file controls the high level logic for the buffer system.
Run this file to control the low level
Microcontrollers which in turn control the hardware.
This file has following classes:
BufferControl
Imports usbCommunication from Autoplant/Gantry (Credit: Philip)
"""

DEBUG = False

class EmergencyInterruptException(Exception):
    pass


class NoTrayReadyException(Exception):
    pass


class BufferControl():
    """
    This class deals with overall workings and logics for the buffer system
    Call this class to create one thread for a buffer tray system
    If both trays are ready, use tray 1
    """
    def __init__(self, arduino_port="/dev/ttyACM0"):
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
            time.sleep(5)
        elif not com_open:
            print("--------------------------------------------------------\n")
            print(colored("COM PORT is not open, please check error logs in terminal", 'red'))
            print("--------------------------------------------------------")   
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
        self.logging = logging
        self.logging.basicConfig(level=logging.DEBUG, filename="thread_logger.log",
                                 filemode="w", format='%(name)s - %(levelname)s - %(message)s '
                                                      '-%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        self.logging.debug("Started high level buffer thread")
        print("Homing Buffer")
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
            if DEBUG:
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

    # # *--------------- Manual API -------------------*

    # def move_buffer_forward(self):
    #     """Send to buffer to move (50mm?) forwards (away from homing position)
    #     """
    #     self.sendMessage("1300000")

    # def move_buffer_backwards(self):
    #     """Send to buffer to move (50mm?) backwards (towards homing position)
    #     """
    #     self.sendMessage("1400000")

    def get_tray_status(self, tray_id=1):
        """Outwards API, call this to check if a tray is ready
        If a tray is ready, return True and which tray 
        Note: Defaults to 1 if both trays are ready

        Args:
            tray_id (int, optional): [Choose tray ID]. Defaults to 1.
        Returns:
            [boolean]: [True = Yes | False = No]
            [int]: [tray id for tray 1 or 2]
            
        """
        return self.tray_ready, self.tray_ready_id

    def get_tray_position(self, tray_id=1):
        """[summary]

        Args:
            tray_id (int, optional): [Choose tray ID]. Defaults to 1.

        Returns:
            [int]: [position in mm]
            [int]: [tray id for tray 1 or 2]
        """
        self.sendMessage("6000000")
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
            time.sleep(0.1)
        return self.tray_position, self.tray_ready_id

    def set_state_machine(self, tray_id=1):
        """Outwards API, when trees have been deposited, call this to start
        state machine
        
        Args:
            tray_id (int, optional): [Choose tray ID]. Defaults to 1.
        """
        self.state_machine_runner()
    
    def set_movement_manual(self, length, direction=0, tray_id=1):
        """[summary]

        Args:
            length (int): [How far to move the tray]
            direction (int, optional): [description]. Defaults to 0.
            tray_id (int, optional): [description]. Defaults to 1.
        """
        #TODO Add Code Here
        #TODO Code needs call to arduino, wait for success and API string
        
    def set_open_cup_manual(self, tray_id=1):
        """[summary]

        Args:
            tray_id (int, optional): [Choose tray ID]. Defaults to 1.
        """
        self.open_tray()

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
            time.sleep(0.1)
        self.tray_ready = True
    
    def state_machine_runner(self):
        if self.state_machine_counter % 2 == 0:
            self.state_machine()
        elif self.state_machine_counter % 2 == 1:
            self.state_machine_two()
        else:
            print(colored("Counter is not of modulus 2, it's %d"% self.state_machine_counter,"green"))
    
    def state_machine_two(self):
        """[State machine from left to right side]
        """
        print(colored("State machine 2", "red"))
        self.ser.reset_input_buffer()
        self.move_tray_state_five()
        time.sleep(0.1)
        self.open_tray()
        time.sleep(0.1)
        self.move_tray_state_four()
        time.sleep(0.1)
        self.open_tray()
        time.sleep(0.1)
        self.move_tray_state_three()
        time.sleep(0.1)
        self.open_tray()
        time.sleep(0.1)
        self.move_tray_state_two()
        time.sleep(0.1)
        self.open_tray()
        time.sleep(0.1)
        self.move_tray_state_one()
        time.sleep(0.1)
        self.open_tray()
        time.sleep(0.1)
        self.move_tray_init()
        # time.sleep(10)
        # print(colored("Restocking!", "red"))
        # self.state_machine_counter += 1
        # print(self.state_machine_counter)
        # self.tray_ready = True

    def state_machine(self):
        """[State machine from right to left side]
        """
        print(colored("State machine 1", "green"))
        self.ser.reset_input_buffer()
        self.move_tray_state_one()
        time.sleep(0.1)
        self.open_tray()
        time.sleep(0.1)
        self.move_tray_state_two()
        time.sleep(0.1)
        self.open_tray()
        time.sleep(0.1)
        self.move_tray_state_three()
        time.sleep(0.1)
        self.open_tray()
        time.sleep(0.1)
        self.move_tray_state_four()
        time.sleep(0.1)
        self.open_tray()
        self.move_tray_state_five()
        time.sleep(0.1)
        self.open_tray()
        self.move_tray_to_restock()
        # print(colored("Restocking!", "green"))
        # time.sleep(10)
        # self.state_machine_counter += 1
        # print(self.state_machine_counter)
        # self.tray_ready = True
                    
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
        if DEBUG:
            print("Open Tray")
        else:
            pass
        self.sendMessage("1800001")
        time.sleep(1.5)
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
        if DEBUG:
            print("state one")
        else:
            pass
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
            time.sleep(0.1)
                

    def move_tray_state_two(self):
        """[Move tray to state two]
        """
        if DEBUG:
            print("state two")
        else:
            pass
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
            time.sleep(0.1)

    def move_tray_state_three(self):
        """[Move tray to state three]
        """
        if DEBUG:
            print("state three")
        else:
            pass
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
            time.sleep(0.1)

    def move_tray_state_four(self):
        """[Move tray to state four]
        """
        if DEBUG:
            print("state four")
        else:
            pass
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
            time.sleep(0.1)

    def move_tray_state_five(self):
        """[Move tray to state five]
        """
        if DEBUG:
            print("state five")
        else:
            pass
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
            time.sleep(0.1)
            
    def move_tray_to_restock(self):
        """[Move tray to restock position]
        """
        if DEBUG:
            print("state restock position")
        else:
            pass
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


if __name__ == '__main__':
    try:
        Buffer_Control = BufferControl("/dev/ttyACM0")
        Buffer_Control.state_machine()
        Buffer_Control.state_machine_two()
    except KeyboardInterrupt:
        print(colored("User Interrupt", "green"))
    except Exception as exp:
        print(exp)
