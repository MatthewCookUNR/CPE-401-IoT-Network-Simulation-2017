from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from uuid import getnode
from ast import literal_eval
import time
import sys
from threading import Thread
from threading import Lock
from threading import Condition
import dropbox

#Thread handles dropbox notifications and use amongst clients
class dropboxThread(Thread):
    def __init__(self, accessToken):
        self.client = dropbox.client.DropboxClient(accessToken)
        Thread.__init__(self, name = "Dropbox Thread")
    def run(self):
        print("Started dropbox notifications thread")
        cursor = None
        while True:
            newState = self.client.delta(cursor)
            cursor = newState['cursor']
            if newState['reset']:
                print('RESET')

            for path, metadata in newState['entries']:
                if metadata is not None:
                    print('%s was created/updated' % path)
                else:
                    print('%s was deleted' % path)

            if not newState['has_more']:
                newChanges = False
            while not newChanges:
                pollResponse = self.client.longpoll_delta(cursor, 120)
                newData = pollResponse
                newChanges = newData['changes']

            if not newChanges:
                print('Timeout, restarting poll')               

#Handles operations for each client device
class clientThread(Thread):
    def __init__(self, number, mySock, address):
        self.sock = mySock
        self.addr = address
        Thread.__init__(self, name = "Thread " + str(number))
        print (self.getName() + " has been initialized\n")
    def run(self):
        OPEN = True # initial value is true, meaning more packets can be sent by the client to server
        while OPEN is True: # OPEN remains true until client quits his connection
            data = self.sock.recv(1024) # waits to recv data from client
            data = bytes.decode(data)
            data = literal_eval(data)
            if data[0] is 1: # 0 is position of code, code of 1 means register message
                locks.conditionTable.acquire()
                print("Lock acquired by " + self.getName())
                while not locks.writeTable:
                    print(self.getName() + " is waiting (lock released)")
                    locks.conditionTable.wait(timeout = 5)
                    print(self.getName() + " stopped waiting (lock reacquired)")
                    locks.writeTable = True
                REGISTER(data[1], data[2] , self.addr[0] , self.addr[1], self.sock )
                locks.writeTable = False
                locks.conditionTable.notify()
                locks.conditionTable.release()
            elif data[0] is 2: # 0 is position of code, code of 1 means deregister message
                locks.conditionTable.acquire()
                print("Lock acquired by " + self.getName())
                while not locks.writeTable:
                    print(self.getName() + " is waiting (lock released)")
                    locks.conditionTable.wait(timeout = 5)
                    print(self.getName() + " stopped waiting (lock reacquired)")
                    locks.writeTable = True
                DEREGISTER(data[1], data[2], self.sock)
                locks.writeTable = False
                locks.conditionTable.notify()
                locks.conditionTable.release()
            elif data[0] is 3: # 0 is position of code, code of 3 means mail message
                locks.conditionBox.acquire()
                print("Lock acquired by " + self.getName())
                while not locks.writeBox:
                    print(self.getName() + " is waiting (lock released)")
                    locks.conditionBox.wait(timeout = 5)
                    print(self.getName() + " stopped waiting (lock reacquired)")
                    locks.writeBox = True
                MSG( data[1], data[2], data[3], time.time() - startTime, self.sock )
                locks.writeBox = False
                locks.conditionBox.notify()
                locks.conditionBox.release()
            elif data[0] is 4: # 0 is position of code, code of 4 means query message
                if data[1] is 1:
                    locks.conditionTable.acquire()
                    print("Lock acquired by " + self.getName())
                    while locks.writeTable:
                        print(self.getName() + " is waiting (lock released)")
                        locks.conditionTable.wait(timeout = 5)
                        print(self.getName() + " stopped waiting (lock reacquired)")
                        locks.writeTable = False
                    QUERY( data[1], data[2], self.sock )
                    locks.writeTable = True
                    locks.conditionTable.notify()
                    locks.conditionTable.release()
                if data[1] is 2:
                    locks.conditionBox.acquire()
                    print("Lock acquired by " + self.getName())
                    while not locks.writeBox:
                        print(self.getName() + " is waiting (lock released)")
                        locks.conditionBox.wait(timeout = 5)
                        print(self.getName() + " stopped waiting (lock reacquired)")
                        locks.writeBox = True
                    QUERY( data[1], data[2], self.sock  )
                    locks.writeBox = False
                    locks.conditionBox.notify()
                    locks.conditionBox.release()
            elif data[0] is 5: # 0 is position of code, code of 5 means quit message
                OPEN = False
                print("Connected device: ", data[1], " is leaving network", "\n")
            elif data[0] is 6: # 0 is position of code, code of 6 means cloud token request
                giveCloudToken(data[1])
            else:
                sys.stdout = logFile2 # switches to printing to error log
                print("malform packet detected from IP: ", self.addr[0])
                sys.stdout = logFile1 # switches back to printing to activity log

#Handles the different mutex locks used by the proxy                
class sharedDataLocks():
    def __init__(self):
        self.deviceTable = [] # initializes table used to store information of registered devices
        self.mailBox = [] # initializes table used to store the mail of clients
        self.writeTable = True
        self.writeBox = True
        self.conditionTable = Condition()
        self.conditionBox = Condition()    

#Registers device onto the server using device's id and MAC address
def REGISTER( deviceID, MAC, IP, port, sock ):
    print ("Device attempting to register to server, input values:")
    print ("DeviceID: ", deviceID, "MAC: ", MAC, "IP: ", IP, "Port: ", port)
    if not deviceTable: # registers device automatically if there are no current devices registered
        registerTime = time.time()- startTime # gets the current elapsed time of the program
        myList = [deviceID, MAC, IP, port, registerTime] # device info to be added to list of registered devices
        deviceTable.append(myList) # adds device to list of registered devices
        mailBox.append([]) # adds a list in the mailbox for device that registered
        print ("Device registered successfully", "\n")
        ACK(1,1, deviceID, 0, 0, sock) # ACK that device registered successfully
    else:
        for index in range(len(deviceTable)): # loops through table of registered devices to check for duplicates or errors
            if(sorted(deviceTable[index][1]) == sorted(MAC)): # looks for duplicate MAC addresses
                if(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks to see if both MAC and deviceID in table are the same as input
                    registerTime = deviceTable[index][4] # time that the device was registered in table of devices
                    mailCount = len(mailBox[index]) # count of messages that are in the mailbox for he specified device
                    print("Device is already registered", "\n")
                    ACK(1,2,deviceID, registerTime, mailCount, sock) # ACK that device is already registered
                else: # Triggers if MAC address inputted is registered to another device
                    print("Device is already registered with same MAC, different device ID", "\n")
                    NACK(1,deviceTable[index][0],MAC, sock) # NACK that such a registered entry exists as triggered above
                return
                    
            elif(sorted(deviceTable[index][0]) == sorted(deviceID)): #looks for duplicate device IDs
                if(sorted(deviceTable[index][1]) == sorted(MAC)): # looks to see if both MAC and deviceID in table are the same as input
                    registerTime = deviceTable[index][4] # time that the device was registered in table of devices
                    mailCount = len(mailBox[index]) # count of messages that are in the mailbox for he specified device
                    print("Device is already registered", "\n")
                    ACK(1,2,deviceID, registerTime, mailCount, sock) # ACK that device is already registered
                else: # Triggers if MAC address inputted is registered to another device
                    print("Device is already registered with same device ID, different MAC address", "\n")
                    NACK(1,deviceID,deviceTable[index][1], sock) # NACK that such a registered entry exists as triggered above
                return
        #Registers device since there were no duplicate MAC addresses or device IDs
        registerTime = time.time()- startTime # gets the current elapsed time of the program
        myList = [deviceID, MAC, IP, port, registerTime] # device info to be added to list of registered devices
        deviceTable.append(myList) # adds device to list of registered devices
        mailBox.append([]) # adds a list in the mailbox to add mail to for the device that was registered
        print ("Device registered successfully", "\n")
        ACK(1,1, deviceID, 0, 0, sock) # ACK that device registered successfully
        return

#Deregisters device from server's stored registry
def DEREGISTER( deviceID, MAC, sock ):
    print("Device attempting to deregister, device ID: ", deviceID, " MAC: ", MAC)
    TableSize = len(deviceTable)
    if(TableSize is 0):
        print("Device failed to deregister", "\n")
        NACK(1,deviceID, MAC, sock)
        return
    for index in range(TableSize): # loops through table of registered devices to check if device is registered
        if(sorted(deviceTable[index][1]) == sorted(MAC)): # looks for duplicate MAC addresses
            if(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks to see if both MAC and device ID in table are the same as input
                deviceTable.remove(deviceTable[index]) # removes entry in table of registered devices for given device deregistering
                print("Device Deregistered, DeviceID: ", deviceID, " MAC: ", MAC,"\n")
                ACK(2,0,deviceID, 0, 0, sock) # ACK that device was deregistered successfully
            else:
                print("Device failed to deregister","\n")
                NACK(2,deviceTable[index][0],MAC, sock) # NACK that device failed to deregister
            return
                    
        elif(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks for duplicate device IDs
            if(sorted(deviceTable[index][1]) == sorted(MAC)): # looks to see if both MAC and device ID in table are the same as input
                deviceTable.remove(deviceTable[index]) # removes entry in table of registered devices for given device deregistering
                print("Device Deregistered, DeviceID: ", deviceID, " MAC: ", MAC,"\n")
                ACK(2,0,deviceID,0,0, sock) # ACK that device was deregistered successfully
            else:
                print("Device failed to deregister","\n")
                NACK(2,deviceID,deviceTable[index][1], sock) # NACK that device failed to deregister
            return
        else:
            print("Device was not registered")
            ACK(2,0, deviceID, 0, 0, sock)
            
#Stores mail between clients in the proxy network
def MSG( fromID, toID, message, time, sock ):
    print("Server attempting to send a message from: ", fromID, " to: ", toID)
    for index in range(len(deviceTable)): # loops through table of registered devices 
        if(sorted(deviceTable[index][0]) == sorted(toID)):# checks to see if device ID is registered with server
            mailBox[index].append([message, time]) # adds message to the mailbox for given dest device ID
            print("Message added by server to the mailbox successfully", "\n")
            ACK(3,0,fromID, 0, 0, sock) # ACK that message was added to mailbox successfully
            return
    print("Destination device ID was not found by server", "\n")
    NACK(3,fromID,0, sock) # NACK that device failed to add message to mailbox, meaning it could not find it in table of registered devices

#Retrieves information stored in the server for client devices
def QUERY(queryType, deviceID, sock):
    if queryType is 1: # query is to obtain info on another registered device
        print("Server attempting to query for info on device ID: ", deviceID)
        for index in range(len(deviceTable)): # loops through table of registered devices
            if(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks to find index of mailbox/table of registered devices
                deviceFound = (0, deviceTable[index][2], deviceTable[index][3]) # Info of device client queried for
                deviceFound = str(deviceFound)
                deviceFound = str.encode(deviceFound)
                print("Server successfully sent info on queried device", "\n")
                sock.send(deviceFound) # send message to client
                return
        print("Server couldn't find the device being queried", "\n")
        NACK(4, deviceID, 0, sock) # NACK that querying device wasn't found in table of registered devices
    if queryType is 2: # query is to obtain mail in mailbox for own device
        print("Server attempting to query for deviceID: ", deviceID, " mail")
        for index in range(len(deviceTable)): # loops through table of registered devices
            if(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks to find device being queried for in table of registered devices
                userMail = (0, mailBox[index]) # Info needed to deliver mail to client
                userMail = str(userMail)
                userMail = str.encode(userMail)
                print("Server sending mail to client")
                sock.send(userMail) # send message to client
                data = sock.recv(1024) # waits for confirmation that mail was sent correctly
                mailBox[index] = [] # empties mailbox of mail that was just sent
                print("Server successfully sent mail, deleting the sent mail from mailbox", "\n")
                return
        print("Server couldn't find the device being queried", "\n")
        NACK(4, deviceID, 0, sock) # NACK that querying device wasn't found in table of registered devices

#Gives client device access to Dropbox cloud
def giveCloudToken(deviceID):
    myReply = str((accessToken))
    byteReply = str.encode(myReply)
    sock.send(byteReply)
    print("Gave cloud access to: ",deviceID, "\n")    
    

#Tells client that a operation was not successful
def NACK(code, deviceID, MAC, sock):
    if code is 1: # code of 1 means register NACK
        myReply = str((1, deviceID, MAC))
        byteReply = str.encode(myReply)
        sock.send(byteReply) # send message to client
    if code is 2: # code of 2 means deregister NACK
        myReply = str((1, deviceID, MAC))
        byteReply = str.encode(myReply)
        sock.send(byteReply) # send message to client
    if code is 3: # code of 3 means MSG NACK
        myReply = str((1, deviceID))
        byteReply = str.encode(myReply)
        sock.send(byteReply) # send message to client
    if code is 4: # code of 4 means query NACK
        myReply = str((1, deviceID))
        byteReply = str.encode(myReply)
        sock.send(byteReply) # send message to client
        
#Tells client that operation was successfull
def ACK( code, flag, deviceID, time, count, sock):
    if code is 1 and flag is 1: # code of 1 means register ACK, flag of 1 means new device registered
        myReply = str((0, flag, deviceID))
        byteReply = str.encode(myReply)
        sock.send(byteReply) # send message to client
    if code is 1 and flag is 2: # code of 1 means register ACK, flag of 2 means device was already registered
        myReply = str((0, flag, deviceID, time, count)) #Tuple to String
        byteReply = str.encode(myReply) #String to Byte
        sock.send(byteReply) # send message to client
    if code is 2: # code of 2 means deregister ACK
        myReply = str((0, deviceID))
        byteReply = str.encode(myReply)
        sock.send(byteReply) # send message to client
    if code is 3: # code of 3 means MSG ACK
        myReply = str((0, deviceID))
        byteReply = str.encode(myReply)
        sock.send(byteReply) # send message to client

#Cloud API setup
appKey = 'liwnilzh5w024rc'
appSecret = 'gt7842fcv8as0oo'
myFlow = dropbox.oauth.DropboxOAuth2FlowNoRedirect(appKey, appSecret)
authorizationURL = myFlow.start()
print ('1. Go to: ' + authorizationURL)
print ('2. Click "Allow" (you might have to log in first)')
print ('3. Copy the authorization code.')
authentiCode = input("Enter the authorization code here: ").strip()
accessToken, userID = myFlow.finish(authentiCode)
cloudNotif = dropboxThread(accessToken)
cloudNotif.start()

#Server Setup Code
portNumber = 9999 # port number for server TCP socket
tcpS = socket(AF_INET, SOCK_STREAM) # initializing new socket
tcpS.bind(('192.168.0.17', portNumber)) # binding server's IP and desired port number to socket
tcpS.listen(5) #5 max queued
threadNumber = 0
locks = sharedDataLocks()
oldStdout = sys.stdout # save old printing setting
logFile1 = open("Activity2.log","w") # open activity log
logFile2 = open("Error2.log","w") # open error log
#sys.stdout = logFile1 # change so print prints to desired file instead of console
print("Server side activity", "\n")
startTime = time.time() # gets starting time of the program
deviceTable = []
mailBox = []
threadList = []
ServerOn = True
while ServerOn is True:
    sock, addr = tcpS.accept() # accepts a connection to the socket
    threadNumber = threadNumber+1
    threadList.append(clientThread(threadNumber, sock, addr))
    threadList[threadNumber-1].start()
sys.stdout = oldStdout # change back to normal printing
logFile1.close() # close activity log file
logFile2.close() # close error log file
        
