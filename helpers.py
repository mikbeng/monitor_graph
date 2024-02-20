from serial.tools.list_ports import comports



def available_ports():
    return [port.device for port in comports()]