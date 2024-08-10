import wifimgr
from time import sleep
import machine
import gc
import network
import json
from machine import Pin, PWM

try:
    import usocket as socket
except:
    import socket

# Initialize PWM and relay IO
pwm = PWM(Pin(6))
pwm.freq(5000)
relays = [Pin(i, Pin.OUT) for i in range(14, 22)]  # Assuming relay pins are from 14 to 21
flag = [False] * 8

# Initialize Wi-Fi using wifimgr
wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass
print("Raspberry Pi Pico W OK")
print("IP address:", wlan.ifconfig()[0])

# HTML to serve
html = """<!DOCTYPE html>
<!-- Add your HTML content here -->
"""

def web_page():
    return html

def get_status():
    return {
        'relay1': flag[0],
        'relay2': flag[1],
        'relay3': flag[2],
        'relay4': flag[3],
        'relay5': flag[4],
        'relay6': flag[5],
        'relay7': flag[6],
        'relay8': flag[7]
    }

def check_for_update():
    # Placeholder function for checking updates
    # Implement your logic here to check for any available updates
    print("Checking for updates...")
    # Return True if an update is available
    return False

def update_firmware():
    # Placeholder function to update firmware
    # Implement your logic here for firmware update
    print("Updating firmware...")
    # Example: download and flash new firmware
    return True

# Create a socket and listen for connections
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
print('Listening on port 80')

def serve_client(conn):
    request = conn.recv(1024)
    request = str(request)
    relay_on = request.find('/relay') >= 0
    all_on = request.find('/all_on') >= 0
    all_off = request.find('/all_off') >= 0
    status_req = request.find('/status') >= 0
    update_req = request.find('/update') >= 0

    if relay_on:
        relay_num = int(request.split('/relay')[1][0])
        flag[relay_num - 1] = not flag[relay_num - 1]
        relays[relay_num - 1].value(flag[relay_num - 1])
        pwm.duty_u16(5000)
        sleep(0.1)
        pwm.duty_u16(0)
        response = f"Relay {relay_num} {'ON' if flag[relay_num - 1] else 'OFF'}"
    elif all_on:
        for i in range(8):
            flag[i] = True
            relays[i].value(True)
        pwm.duty_u16(5000)
        sleep(0.1)
        pwm.duty_u16(0)
        response = "All Relays ON"
    elif all_off:
        for i in range(8):
            flag[i] = False
            relays[i].value(False)
        pwm.duty_u16(5000)
        sleep(0.1)
        pwm.duty_u16(0)
        response = "All Relays OFF"
    elif status_req:
        response = json.dumps(get_status())
    elif update_req:
        if check_for_update():
            update_firmware()
            response = "Firmware Updated"
        else:
            response = "No Update Available"
    else:
        response = web_page()

    conn.send('HTTP/1.1 200 OK\r\n')
    if status_req or update_req:
        conn.send('Content-Type: application/json\r\n')
    else:
        conn.send('Content-Type: text/html\r\n')
    conn.send('Connection: close\r\n\r\n')
    conn.sendall(response)
    conn.close()

while True:
    try:
        if gc.mem_free() < 102000:
            gc.collect()
        conn, addr = s.accept()
        conn.settimeout(3.0)
        print('Received HTTP GET connection request from %s' % str(addr))
        serve_client(conn)
    except OSError as e:
        conn.close()
        print('Connection closed')
