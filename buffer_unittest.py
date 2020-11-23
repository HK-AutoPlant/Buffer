import unittest
from buffer_high_level import BufferControl

controller = BufferControl('/dev/ttyACM0')
class TestBufferInOut(unittest.TestCase):

    def test_out_reset(self):
        self.assertEqual(controller.move_tray_init, "100")
    
    def test_state_1(self):
        self.assertEqual(controller.move_tray_state_one, "111")

    def test_state_2(self):
        self.assertEqual(controller.move_tray_state_two, "121")
        
    def test_state_3(self):
        self.assertEqual(controller.move_tray_state_three, "131")
        
    def test_state_4(self):
        self.assertEqual(controller.move_tray_state_four, "141")
        
    def test_state_5(self):
        self.assertEqual(controller.move_tray_state_five, "151")

    def test_plants_out(self):
        self.assertEqual(controller.check_plants,"106")
    
    def test_position_out(self):
        self.assertEqual(controller.check_position, "107")

if __name__ == "__main__":
    unittest.main()