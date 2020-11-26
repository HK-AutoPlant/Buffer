from buffer_high_level import BufferControl
from termcolor import colored

testing_api = BufferControl("/dev/ttyUSB0")
var_a,var_b = testing_api.is_tray_ready()
if var_a:
    print(colored("Starting state machine via API", "green"))
    testing_api.trees_dropped()