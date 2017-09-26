import websocket
import json
import uuid
import os
import hmac
import hashlib
import time
import threading
import re
import string

def clean(s):
    return filter(lambda x: x in (string.lowercase + "_"), s.lower())

fmt = open('fmt.txt').read()

a = re.findall(r'addVariable\(data\.(.*?)\s*,\s*(\-*\d+)\s*,\s*(\-*\d+)\s*,\s*(\-*\d+)\s*\);(.*?)$', fmt, re.MULTILINE)

print a
vars = []
for var in a:
    n = clean(var[0])
    if var[4] != '':
       n = var[4].replace('//','').rstrip().lstrip()
    n = n.replace(' ','_')
    vars.append([n, int(var[1]), int(var[2]), int(var[3])])
    print vars[-1]

msg = "03412bef7c94ca662392245bff5ccca20000010445140000000176031831f101801443041c44000000000003c00608b0003412bef7c94ca662392245bff5ccca20000010445140000000176031831f101801443041c44000000000003c00608b00"
inp = ""
out = ["0000","0001",'0010','0011','0100','0101','0110','0111','1000','1001','1010','1011','1100','1101','1110','1111']
for i in msg:
    inp += out[int(i,16)]

tot = 0
for name, min, max, bits in vars:
    x = inp[0:bits]
    inp = inp[bits:] 
    tot += bits
    x = int(x, 2)
    v = min + (max-min) * x / (2**bits - 1.)
    print name, v
print tot, tot/8.

lock = threading.Lock()
lock.acquire()

count = 0
recv = 0

def whine(ws, error):
    print "[WS] Got error: "+str(error)

def ohp(ws):
    print "[WS] Connection unexpectedly dropped. Retrying..."
    ws.close()

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
s = serial.Serial('/dev/ttyAMA0', 57600)

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
        rssi = ord(sp[0])
        print sp
        #ln = ord(sp[1])
        ln = 60
        msg = ','.join(sp[2:])
        aa = msg[:ln]
        inp = ""
        for c in aa:
           num = ord(c)
           for i in [1,2,4,8,16,32,64,128][::-1]:
              inp += ("1" if (num & i) else "0")
        print inp
        dd = {"id":str(uuid.uuid4()), "mission": 39, "timestamp": int(time.time()*1000), "raw": msg[ln:].encode('hex'), "received": msg[:ln].encode('hex')}
        for name, min, max, bits in vars:
            x = inp[0:bits]
            inp = inp[bits:]
            x = int(x, 2)
            v = min + (max-min) * x / (2**bits - 1.)
            dd[name] = v
            print name, v
        print dd.keys()
        #print "actual thing received", msg[:ln]
        #print "raw bytestring", msg[ln:]
        
        ws.send(json.dumps(dd))

    except ImportError:
        print "Error parsing"

while True:
    b = ord(s.read(1))
    rolling.append(b)
    if len(rolling) > 4:
        rolling = rolling[1:]
    if rolling == START:
        parsing = True
        message = []
    elif rolling == END:
        parsing = False
        parse_message(message[:-3])
    elif parsing:
        message.append(b)
