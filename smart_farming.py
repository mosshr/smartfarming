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

# HTML to serve (as defined above)
html = """<!DOCTYPE html>
<html>
<head>
    <title>Smart Farming Control</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        button { padding: 10px 20px; font-size: 16px; margin: 10px; cursor: pointer; }
    </style>
    <script>
        function sendRequest(path) {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', path, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    alert(xhr.responseText);
                }
            };
            xhr.send();
        }

        function checkForUpdate() {
            sendRequest('/update_check');
        }

        function performUpdate() {
            sendRequest('/update');
        }
    </script>
</head>
<body>
    <h1>Smart Farming Control</h1>
    <button onclick="sendRequest('/all_on')">Turn All Relays On</button>
    <button onclick="sendRequest('/all_off')">Turn All Relays Off</button>
    <br>
    <button onclick="checkForUpdate()">Check for Updates</button>
    <button onclick="performUpdate()">Perform Update</button>
</body>
</html>
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
    print("Checking for updates...")
    # Return True if an update is available
    return False

def update_firmware():
    # Placeholder function to update firmware
    print("Updating firmware...")
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
    update_check_req = request.find('/update_check') >= 0
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
    elif update_check_req:
        if check_for_update():
            response = "Update Available"
        else:
            response = "No Update Available"
    elif update_req:
        if update_firmware():
            response = "Firmware Updated"
        else:
            response = "Update Failed"
    else:
        response = web_page()

    conn.send('HTTP/1.1 200 OK\r\n')
    if status_req or update_check_req or update_req:
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
