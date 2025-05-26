import threading
import queue
import time
import smbus
from ble_utils.bluetooth_uart_server import ble_gatt_uart_loop, get_ble_mac

# LCD constants
LCD_I2C_ADDR = 0x27  
LCD_WIDTH = 16
LCD_CHR = 1
LCD_CMD = 0
LINE_1 = 0x80
LINE_2 = 0xC0
ENABLE = 0b00000100
E_PULSE = 0.0005
E_DELAY = 0.0005

class LCD:
    def __init__(self, addr=LCD_I2C_ADDR, bus=1):  
        self.bus = smbus.SMBus(bus)
        self.addr = addr
        self._init_lcd()

    def _init_lcd(self):
        self._lcd_byte(0x33, LCD_CMD)
        self._lcd_byte(0x32, LCD_CMD)
        self._lcd_byte(0x06, LCD_CMD)
        self._lcd_byte(0x0C, LCD_CMD)
        self._lcd_byte(0x28, LCD_CMD)
        self._lcd_byte(0x01, LCD_CMD)
        time.sleep(E_DELAY)

    def _lcd_byte(self, bits, mode):
        bits_high = mode | (bits & 0xF0) | 0x08
        bits_low = mode | ((bits << 4) & 0xF0) | 0x08
        self.bus.write_byte(self.addr, bits_high)
        self._toggle_enable(bits_high)
        self.bus.write_byte(self.addr, bits_low)
        self._toggle_enable(bits_low)

    def _toggle_enable(self, bits):
        time.sleep(E_DELAY)
        self.bus.write_byte(self.addr, bits | ENABLE)
        time.sleep(E_PULSE)
        self.bus.write_byte(self.addr, bits & ~ENABLE)
        time.sleep(E_DELAY)

    def clear(self):
        self._lcd_byte(0x01, LCD_CMD)

    def message(self, text, line=LINE_1):
        text = text.ljust(LCD_WIDTH)
        self._lcd_byte(line, LCD_CMD)
        for char in text:
            self._lcd_byte(ord(char), LCD_CHR)

def main():
    print("[app] Adapter MAC:", get_ble_mac())

    rx_q = queue.Queue()
    tx_q = queue.Queue()
    device_name = "piofnat"
    evt_q = queue.Queue()

    # Initialize LCD and show device name
    lcd = LCD() 
    lcd.message(f"Device: {device_name}", LINE_1)

    threading.Thread(target=ble_gatt_uart_loop, args=(rx_q, tx_q, device_name, evt_q), daemon=True).start()
    try:         
        while True:
            try:
                incoming = rx_q.get_nowait()
                print("In main loop: {}".format(incoming))
                lcd.message(str(incoming)[:LCD_WIDTH], LINE_2)  
            except queue.Empty:
                pass
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        lcd.clear()  

if __name__ == '__main__':
    main()
