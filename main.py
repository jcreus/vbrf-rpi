import websocket
import json
import uuid
import os
import hmac
import hashlib
import time
import threading
import pandas as pd

df = pd.read_hdf('/home/joan/valbal/datasets/ssi54/ssi54.h5', stop=1000)

lock = threading.Lock()
lock.acquire()

def whine(ws, error):
    print "[WS] Got error: "+str(error)

def ohp(ws):
    print "[WS] Connection unexpectedly dropped. Retrying..."

def opened(ws):
    print "[WS] Connection opened"
    lock.release()

def msg(ws, message):
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

lst = df.to_dict('records')
for i in range(1000):
    print "Sending message"
    dic = { "id":str(uuid.uuid4()), "mission":39, "timestamp": int(time.time()*1000)}
    dic.update(lst[i])
    ws.send(json.dumps(dic))
    time.sleep(0.95)
