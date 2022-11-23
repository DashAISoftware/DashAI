# Este archivo corre al hacer import DashAI
from subprocess import Popen
import webbrowser
import os
import time
import signal

url = "http://localhost:3000/"

procs = [
    Popen('python main.py', shell=True, cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)) ,'back')), 
    Popen('python -m http.server 3000', shell=True, cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)) ,'front/build'))
    ]
def handler(signum, frame):
    print("\nShutting down DashAI")
    for p in procs:
        p.terminate()
    time.sleep(2)
signal.signal(signal.SIGINT, handler)
time.sleep(1)
webbrowser.open(url, new=0, autoraise=True)

for p in procs:
   p.wait()
