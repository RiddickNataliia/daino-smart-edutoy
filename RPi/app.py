import threading
import queue
import time

# Bluez gatt uart service (SERVER)
from ble_utils.bluetooth_uart_server import ble_gatt_uart_loop, get_ble_mac

# TODO: 1) print BLE device name on LCD on app start
# TODO: 2) print incoming bluetooth messages on LCD



def main():
    print("[app] Adapter MAC:", get_ble_mac())

    rx_q = queue.Queue()
    tx_q = queue.Queue()
    device_name = "your-device-name" # TODO: replace with your own (unique) device name
    evt_q = queue.Queue()          # New queue which provides the connection state of our ble server

    threading.Thread(target=ble_gatt_uart_loop, args=(rx_q, tx_q, device_name, evt_q), daemon=True).start()
    try:         
        while True:
            try:
                incoming = rx_q.get_nowait()
                print("In main loop: {}".format(incoming))
            except queue.Empty:
                pass # nothing in Q 
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        # TODO: maybe cleanup if needed or code get's extended
        pass
        
if __name__ == '__main__':
    main()