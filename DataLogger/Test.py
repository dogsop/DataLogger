import os
import signal
import sys
import json
import time
import socket
import subprocess
import threading
import http.client
import urllib.parse

if os.path.isfile("/home/ken/Projects/NewRasPi/DataLogger/pidSettings.json") == False:
    pidSettings = { "Kp": 1.1, "Ki": 2.2, "Kd": 3.3 }
    with open('/home/ken/Projects/NewRasPi/DataLogger/pidSettings.json', 'w') as f:
        json.dump(pidSettings, f)
        
