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
import datetime



def signal_handler(sig, frame):
    global lcdControlProcess
    global runTempMonitorLoop
    global runPidMonitorLoop
    global runRemoteMonitorLoop
    print('You pressed Ctrl+C!')
    print("Killing monitor...")
    runTempMonitorLoop = False
    runPidMonitorLoop = False
    runRemoteMonitorLoop = False
    lcdControlProcess.send_signal(signal.SIGINT)
    #os.kill(os.getpid(), signal.SIGUSR1)
    return

def monitorRemoteAppLoop():
    global runRemoteMonitorLoop
    global pidSettings
    global setPointSettings
    
    print ("in monitorRemoteAppLoop")
    
    while runRemoteMonitorLoop == True:
        print ("in monitorRemoteAppLoop looping")
        
        connection = http.client.HTTPSConnection('api.parse.com', 443)
        connection.connect()
        connection.request('GET', '/1/classes/PidSettings/' + pidSettings['objectId'], '', {
               "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
               "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
             })
        
        result = json.loads(connection.getresponse().read().decode())
        #print (result)
        
        #print ("result['updatedAt'] - #%s#" % result['updatedAt'])
        #print ("pidSettings['updatedAt'] - #%s#" % pidSettings['updatedAt'])
        
        if result['updatedAt'] != pidSettings['updatedAt']:
            print('record has been updated')
            pidSettings['Kp'] = result['Kp']
            pidSettings['Kd'] = result['Kd']
            pidSettings['Ki'] = result['Ki']
            pidSettings['updatedAt'] = result['updatedAt']
            with open('/home/pi/SmokerController/pidSettings.json', 'w') as f:
                json.dump(pidSettings, f, ensure_ascii=False)
            lcdControlProcess.send_signal(signal.SIGUSR1)
            #print (" ")
        
        connection = http.client.HTTPSConnection('api.parse.com', 443)
        connection.connect()
        connection.request('GET', '/1/classes/SetPointSettings/' + setPointSettings['objectId'], '', {
               "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
               "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
             })
        
        result = json.loads(connection.getresponse().read().decode())
        #print (result)

        #print ("result['updatedAt'] - #%s#" % result['updatedAt'])
        #print ("setPointSettings['updatedAt'] - #%s#" % setPointSettings['updatedAt'])
        
        if result['updatedAt'] != setPointSettings['updatedAt']:
            print('record has been updated')
            setPointSettings['SetPointTemp'] = result['SetPointTemp']
            setPointSettings['ControllerRunning'] = result['ControllerRunning']
            setPointSettings['updatedAt'] = result['updatedAt']
            with open('/home/pi/SmokerController/setPoint.json', 'w') as f:
                json.dump(setPointSettings, f, ensure_ascii=False)
            lcdControlProcess.send_signal(signal.SIGUSR1)
            #print (" ")
        
        time.sleep(20)
        
    print ("exiting monitorRemoteAppLoop")
    return

def monitorTempLoop():
    global runTempMonitorLoop
    UDP_IP = "127.0.0.1"
    UDP_PORT = 9930
    
    print ("in monitorTempLoop")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    #sock.setblocking(False)
    sock.settimeout(15.0)
    
    while runTempMonitorLoop == True:
        # receive from peer
        try:
            print( "monitorTempLoopcalling sock.recvfrom")
            data, addr = sock.recvfrom(1024)
            #print( "calling data.decode")
            dataString = data.decode("utf-8")
            #print( "dataString = #" + dataString + "#")
            #print( "calling json.loads")
            tempData = json.loads(dataString)
            print(tempData)
            connection = http.client.HTTPSConnection('api.parse.com', 443)
            connection.connect()
            connection.request('POST', '/1/classes/RealTimeTempData', json.dumps(tempData), 
                {
                "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
                "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
                "Content-Type": "application/json"
                })
            result = json.loads(connection.getresponse().read().decode())
            print (result)        
            #print (" ")
        # if the receiving fails, print something to notify the user
        except socket.timeout as e:
            print ("monitorTempLoop timeout({0}): {1}".format(e.errno, e.strerror))
        except socket.error as e:
            print ("monitorTempLoop I/O error({0}): {1}".format(e.errno, e.strerror))
        except:
            print ("monitorTempLoop Unexpected error:", sys.exc_info()[0])
        #time.sleep(2)
    print ("exiting monitorTempLoop")
    return

def monitorPidLoop():
    global runPidMonitorLoop
    UDP_IP = "127.0.0.1"
    UDP_PORT = 9931
    
    print ("in monitorPidLoop")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    #sock.setblocking(False)
    sock.settimeout(45.0)
    
    while runPidMonitorLoop == True:
        # receive from peer
        try:
            print( "monitorPidLoop calling sock.recvfrom")
            data, addr = sock.recvfrom(1024)
            #print( "calling data.decode")
            dataString = data.decode("utf-8")
            #print( "dataString = #" + dataString + "#")
            #print( "calling json.loads")
            tempData = json.loads(dataString)
            print(tempData)
            connection = http.client.HTTPSConnection('api.parse.com', 443)
            connection.connect()
            connection.request('POST', '/1/classes/RealTimePidData', json.dumps(tempData), 
                {
                "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
                "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
                "Content-Type": "application/json"
                })
            result = json.loads(connection.getresponse().read().decode())
            print (result)        
            #print (" ")
        # if the receiving fails, print something to notify the user
        except socket.timeout as e:
            print ("monitorPidLoop timeout({0}): {1}".format(e.errno, e.strerror))
        except socket.error as e:
            print ("monitorPidLoop I/O error({0}): {1}".format(e.errno, e.strerror))
        except:
            print ("monitorPidLoop Unexpected error:", sys.exc_info()[0])
        #time.sleep(2)
    print ("exiting monitorPidLoop")
    return

def initPidSettings():
    global pidSettings
    
    print("initPidSettings...")
    pidSettings = { "Kp": 0.1, "Ki": 0.002, "Kd": 1.0 }
    
    connection = http.client.HTTPSConnection('api.parse.com', 443)
    params = urllib.parse.urlencode({"order":"-createdAt","limit":1})
    connection.connect()
    connection.request('GET', '/1/classes/PidSettings?%s' % params, '', {
           "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
           "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
         })
    
    result = json.loads(connection.getresponse().read().decode())
    print (result)
    print (" ")
    
    if 'results' in result.keys():
        array = result['results']
        print (array)
        print (" ")
        if len(array) > 0:
            #print ("found one")
            currentPidSettings = array[0]
            pidSettings['Kp'] = currentPidSettings['Kp']
            pidSettings['Kd'] = currentPidSettings['Kd']
            pidSettings['Ki'] = currentPidSettings['Ki']
            pidSettings['objectId'] = currentPidSettings['objectId']
            pidSettings['updatedAt'] = currentPidSettings['updatedAt']
            #print(updateType)
        else:
            #print ("creating record")
            #print (pidSettings)
            connection.request('POST', '/1/classes/PidSettings', json.dumps(pidSettings), {
                "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
                "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
                "Content-Type": "application/json"
                })
            result = json.loads(connection.getresponse().read().decode())
            #print (result)        
            #print (" ")
            pidSettings['objectId'] = result['objectId']
            pidSettings['updatedAt'] = result['createdAt']
            #print(updateType)
        
    with open('/home/pi/SmokerController/pidSettings.json', 'w') as f:
        json.dump(pidSettings, f, ensure_ascii=False)
    print(pidSettings)        
    

def initSetPointSettings():
    global setPointSettings

    print("initSetPointSettings...")
    setPointSettings = { "SetPointTemp": 225, "ControllerRunning": False }
    
    connection = http.client.HTTPSConnection('api.parse.com', 443)
    params = urllib.parse.urlencode({"order":"-createdAt","limit":1})
    connection.connect()
    connection.request('GET', '/1/classes/SetPointSettings?%s' % params, '', {
           "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
           "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
         })
    
    result = json.loads(connection.getresponse().read().decode())
    print (result)
    #print (" ")
    
    if 'results' in result.keys():
        array = result['results']
        #print (array)
        #print (" ")
        if len(array) > 0:
            #print ("found one")
            currentSetPointSettings = array[0]
            setPointSettings['SetPointTemp'] = currentSetPointSettings['SetPointTemp']
            setPointSettings['ControllerRunning'] = currentSetPointSettings['ControllerRunning']
            setPointSettings['objectId'] = currentSetPointSettings['objectId']
            setPointSettings['updatedAt'] = currentSetPointSettings['updatedAt']
        else:
            #print ("creating record")
            #print (setPointSettings)
            connection.request('POST', '/1/classes/SetPointSettings', json.dumps(setPointSettings), {
                "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
                "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
                "Content-Type": "application/json"
                })
            result = json.loads(connection.getresponse().read().decode())
            #print (result)        
            #print (" ")
            setPointSettings['objectId'] = result['objectId']
            setPointSettings['updatedAt'] = result['createdAt']
        
    with open('/home/pi/SmokerController/setPoint.json', 'w') as f:
        json.dump(setPointSettings, f, ensure_ascii=False)
    print(setPointSettings)        

def initTempData():
    
    print("initTempData...")
    
    connection = http.client.HTTPSConnection('api.parse.com', 443)
    params = urllib.parse.urlencode({"order":"-createdAt","limit":1})
    connection.connect()
    connection.request('GET', '/1/classes/RealTimeTempData?%s' % params, '', {
           "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
           "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
         })
    
    result = json.loads(connection.getresponse().read().decode())
    print (result)
    print (" ")
    
    if 'results' in result.keys():
        array = result['results']
        print (array)
        print (" ")
        if len(array) > 0:
            #print ("found one")
            lastTempData = array[0]
            lastTempReadingString = lastTempData['updatedAt']
            print(lastTempReadingString)
            #2014-07-29T03:25:19.054Z
            lastTempReading = datetime.datetime.strptime(lastTempReadingString, '%Y-%m-%dT%H:%M:%S.%fZ')
            print(lastTempReading)
            currentTime = datetime.datetime.now(datetime.timezone.utc)
            print(currentTime)
            currentTimeNaive = currentTime.replace(tzinfo=None)
            print(currentTimeNaive)
            deltaTime = currentTimeNaive - lastTempReading
            print(deltaTime)
            if deltaTime.total_seconds() > 12 * 60 * 60:
                print('Old data, resetting')
                cleanTempDataClass()
                cleanPidDataClass()
            else:
                print('Resuming')
                
            #print(updateType)
        
    
def cleanTempDataClass():
    
    print("cleanTempDataClass...")
    
    readDataFlag = True
    
    while readDataFlag == True:
        connection = http.client.HTTPSConnection('api.parse.com', 443)
        connection.connect()
        connection.request('GET', '/1/classes/RealTimeTempData', '', {
               "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
               "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
             })
        result = json.loads(connection.getresponse().read().decode())
        
        if 'results' in result.keys():
            array = result['results']
            print (array)
            print (len(array))
            print (" ")
            if len(array) > 0:
                #print ("found one")
                for lastTempData in array:
                    objectId = lastTempData['objectId']
                    print ("deleting object {0}".format(objectId))
                    delConnection = http.client.HTTPSConnection('api.parse.com', 443)
                    delConnection.connect()
                    delConnection.request('DELETE', '/1/classes/RealTimeTempData/%s' % objectId, '', {
                           "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
                           "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL"
                         })
                    result = json.loads(delConnection.getresponse().read().decode())
                    print(result)
            else:
                print ("class is empty")
                readDataFlag = False
        else:
            readDataFlag = False
        
def cleanPidDataClass():
    
    print("cleanPidDataClass...")
    
    readDataFlag = True
    
    while readDataFlag == True:
        connection = http.client.HTTPSConnection('api.parse.com', 443)
        connection.connect()
        connection.request('GET', '/1/classes/RealTimePidData', '', {
               "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
               "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL",
             })
        result = json.loads(connection.getresponse().read().decode())
        
        if 'results' in result.keys():
            array = result['results']
            print (array)
            print (len(array))
            print (" ")
            if len(array) > 0:
                #print ("found one")
                for lastTempData in array:
                    objectId = lastTempData['objectId']
                    print ("deleting object {0}".format(objectId))
                    delConnection = http.client.HTTPSConnection('api.parse.com', 443)
                    delConnection.connect()
                    delConnection.request('DELETE', '/1/classes/RealTimePidData/%s' % objectId, '', {
                           "X-Parse-Application-Id": "LPO7xM2lmiSxjklrtU2qGRU0ZGYEyismSvUmO55X",
                           "X-Parse-REST-API-Key": "6RWHWV9kp3fqAu8tv0KY0P7Aa1INWMustGCHYvJL"
                         })
                    result = json.loads(delConnection.getresponse().read().decode())
                    print(result)
            else:
                print ("class is empty")
                readDataFlag = False
        else:
            readDataFlag = False

    
print("Starting...")
signal.signal(signal.SIGINT, signal_handler)

initTempData()
initPidSettings()
initSetPointSettings()

print(setPointSettings)
print(pidSettings)
        
monitorTempThread = threading.Thread(name='daemon1', target=monitorTempLoop)
runTempMonitorLoop = True
monitorTempThread.start()

monitorPidThread = threading.Thread(name='daemon2', target=monitorPidLoop)
runPidMonitorLoop = True
monitorPidThread.start()

monitorRemoteAppThread = threading.Thread(name='daemon3', target=monitorRemoteAppLoop)
runRemoteMonitorLoop = True
monitorRemoteAppThread.start()

lcdControlProcess = subprocess.Popen(['/usr/local/bin/LCDControl'])
lcdControlProcess.wait()

print("Sleeping...")
monitorTempThread.join()
monitorPidThread.join()
monitorRemoteAppThread.join()

print("Exiting...")
