import websocket
import json
import uuid
import os
import hmac
import hashlib
import time
import threading

lock = threading.Lock()
lock.acquire()

count = 0
recv = 0

def whine(ws, error):
    print "[WS] Got error: "+str(error)

def ohp(ws):
    print "[WS] Connection unexpectedly dropped. Retrying..."

def opened(ws):
    print "[WS] Connection opened"
    lock.release()

def msg(ws, message):
    global count
    if 'success' in message:
        count += 1
    if 'receive' in message:
        recv += 1
    print "[WS] Got message", message

def run_connection():
    global ws
    while True:
        t = time.time()*1000.
        sign = t, hmac.new(os.environ['KAI_KEY'], str(int(t)), hashlib.sha256).hexdigest()
        ws = websocket.WebSocketApp("wss://nasonov-writer.herokuapp.com/%d/%s" % sign,
                                    on_error=whine,
                                    on_message=msg,
                                    on_close=ohp,
                                    on_open=opened)
        ws.run_forever()


t = threading.Thread(target=run_connection)
t.daemon = True
t.start()

lock.acquire()
print "Okay, we're in business"

import serial
s = serial.Serial('/dev/ttyACM0', 115200)

rolling = []

START = [204, 105, 119, 82]
END = [162, 98, 128, 161]

parsing = False
message = []

def parse_message(msg):
    print "Parsing", msg
    try:
        msg = ''.join(map(chr, msg))
        sp = msg.split(',')
        ln = int(sp[0])
        msg = ','.join(msg[1:])
        print "actual thing received", msg[:ln]
        print "raw bytestring", msg[ln:]

    except:
        print "Error parsing"

while True:
    b = ord(s.read(1))
    rolling.append(b)
    if len(rolling) > 4:
        rolling = rolling[1:]
    if rolling == START:
        parsing = True
        message = []
    if rolling == END:
        parsing = False
        parse_message(message[:-3])

    if parsing:
        message.append(b)
