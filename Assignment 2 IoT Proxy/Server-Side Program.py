from socket import socket, AF_INET, SOCK_STREAM
from uuid import getnode
from ast import literal_eval
import time
import sys

def REGISTER( deviceID, MAC, IP, port ):
    print ("Device attempting to register to server, input values:")
    print ("DeviceID: ", deviceID, "MAC: ", MAC, "IP: ", IP, "Port: ", port)
    if not deviceTable: # registers device automatically if there are no current devices registered
        registerTime = time.time()- startTime # gets the current elapsed time of the program
        myList = [deviceID, MAC, IP, port, registerTime] # device info to be added to list of registered devices
        deviceTable.append(myList) # adds device to list of registered devices
        mailBox.append([]) # adds a list in the mailbo to add mail to for the device that was registered
        print ("Device registered successfully", "\n")
        ACK(1,1, deviceID, 0, 0) # ACK that device registered successfully
    else:
        for index in range(len(deviceTable)): # loops through table of registered devices to check for duplicates or errors
            if(sorted(deviceTable[index][1]) == sorted(MAC)): # looks for duplicate MAC addresses
                if(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks to see if both MAC and deviceID in table are the same as input
                    registerTime = deviceTable[index][4] # time that the device was registered in table of devices
                    mailCount = len(mailBox[index]) # count of messages that are in the mailbox for he specified device
                    print("Device is already registered", "\n")
                    ACK(1,2,deviceID, registerTime, mailCount) # ACK that device is already registered
                else: # Triggers if MAC address inputted is registered to another device
                    print("Device is already registered with same MAC, different device ID", "\n")
                    NACK(1,deviceTable[index][0],MAC) # NACK that such a registered entry exists as triggered above
                return
                    
            elif(sorted(deviceTable[index][0]) == sorted(deviceID)): #looks for duplicate device IDs
                if(sorted(deviceTable[index][1]) == sorted(MAC)): # looks to see if both MAC and deviceID in table are the same as input
                    registerTime = deviceTable[index][4] # time that the device was registered in table of devices
                    mailCount = len(mailBox[index]) # count of messages that are in the mailbox for he specified device
                    print("Device is already registered", "\n")
                    ACK(1,2,deviceID, registerTime, mailCount) # ACK that device is already registered
                else: # Triggers if MAC address inputted is registered to another device
                    print("Device is already registered with same device ID, different MAC address", "\n")
                    NACK(1,deviceID,deviceTable[index][1]) # NACK that such a registered entry exists as triggered above
                return
        #Registers device since there were no duplicate MAC addresses or device IDs
        registerTime = time.time()- startTime # gets the current elapsed time of the program
        myList = [deviceID, MAC, IP, port, registerTime] # device info to be added to list of registered devices
        deviceTable.append(myList) # adds device to list of registered devices
        mailBox.append([]) # adds a list in the mailbo to add mail to for the device that was registered
        print ("Device registered successfully", "\n")
        ACK(1,1, deviceID, 0, 0) # ACK that device registered successfully
        return

def DEREGISTER( deviceID, MAC ):
    print("Device attempting to deregister, device ID: ", deviceID, " MAC: ", MAC)
    TableSize = len(deviceTable)
    if(TableSize is 0):
        print("Device failed to deregister", "\n")
        NACK(1,deviceID, MAC)
        return
    for index in range(TableSize): # loops through table of registered devices to check if device is registered
        if(sorted(deviceTable[index][1]) == sorted(MAC)): # looks for duplicate MAC addresses
            if(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks to see if both MAC and device ID in table are the same as input
                deviceTable.remove(deviceTable[index]) # removes entry in table of registered devices for given device deregistering
                print("Device Deregistered, DeviceID: ", deviceID, " MAC: ", MAC,"\n")
                ACK(1,1,deviceID, 0, 0) # ACK that device was deregistered successfully
            else:
                print("Device failed to deregister","\n")
                NACK(1,deviceTable[index][0],MAC) # NACK that device failed to deregister
            return
                    
        elif(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks for duplicate device IDs
            if(sorted(deviceTable[index][1]) == sorted(MAC)): # looks to see if both MAC and device ID in table are the same as input
                deviceTable.remove(deviceTable[index]) # removes entry in table of registered devices for given device deregistering
                print("Device Deregistered, DeviceID: ", deviceID, " MAC: ", MAC,"\n")
                ACK(2,0,deviceID,0,0) # ACK that device was deregistered successfully
            else:
                print("Device failed to deregister","\n")
                NACK(2,deviceID,deviceTable[index][1]) # NACK that device failed to deregister
            return
    
def MSG( fromID, toID, message, time ):
    print("Server attempting to send a message from: ", fromID, " to: ", toID)
    for index in range(len(deviceTable)): # loops through table of registered devices 
        if(sorted(deviceTable[index][0]) == sorted(toID)):# checks to see if dest device ID is registered with server
            mailBox[index].append([message, time]) # adds message to the mailbox for given dest device ID
            print("Message added by server to the mailbox successfully", "\n")
            ACK(3,0,fromID, 0, 0) # ACK that message was added to mailbox successfully
            return
    print("Destination device ID was not found by server", "\n")
    NACK(3,fromID,0) # NACK that device failed to add message to mailbox, meaning it could not find it in table of registered devices

def QUERY(queryType, deviceID):
    if queryType is 1: # query is to obtain info on another registered device
        print("Server attempting to query for info on device ID: ", deviceID)
        for index in range(len(deviceTable)): # loops through table of registered devices
            if(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks to find index of mailbox/table of registered devices
                deviceFound = (0, deviceTable[index][2], deviceTable[index][3]) # Info of device client queried for
                deviceFound = str(deviceFound) # tuple to str
                deviceFound = str.encode(deviceFound) # str to bytes
                print("Server successfully sent info on queried device", "\n")
                sock.send(deviceFound) # send message to client
                return
        print("Server couldn't find the device being queried", "\n")
        NACK(4, deviceID, 0) # NACK that querying device wasn't found in table of registered devices
    if queryType is 2: # query is to obtain mail in mailbox for own device
        print("Server attempting to query for deviceID: ", deviceID, " mail")
        for index in range(len(deviceTable)): # loops through table of registered devices
            if(sorted(deviceTable[index][0]) == sorted(deviceID)): # looks to find device being queried for in table of registered devices
                userMail = (0, mailBox[index]) # Info needed to deliver mail to client
                userMail = str(userMail) # tuple to str
                userMail = str.encode(userMail) # str to bytes
                print("Server sending mail to client")
                sock.send(userMail) # send message to client
                data = sock.recv(1024) # waits for confirmation that mail was sent correctly
                mailBox[index] = [] # empties mailbox of mail that was just sent
                print("Server successfully sent mail, deleting the sent mail from mailbox", "\n")
                return
        print("Server couldn't find the device being queried", "\n")
        NACK(4, deviceID, 0) # NACK that querying device wasn't found in table of registered devices
        

def NACK(code, deviceID, MAC):
    if code is 1: # code of 1 means register ACK
        myReply = str((1, deviceID, MAC)) #Tuple to String
        byteReply = str.encode(myReply) #String to Byte
        sock.send(byteReply) # send message to client
    if code is 2: # code of 2 means deregister ACK
        myReply = str((1, deviceID, MAC)) #T uple to String
        byteReply = str.encode(myReply) # String to Byte
        sock.send(byteReply) # send message to client
    if code is 3: # code of 3 means MSG NACK
        myReply = str((1, deviceID)) #Tuple to String
        byteReply = str.encode(myReply) #String to Byte
        sock.send(byteReply) # send message to client
    if code is 4: # code of 4 means query NACK
        myReply = str((1, deviceID)) #Tuple to String
        byteReply = str.encode(myReply) #String to Byte
        sock.send(byteReply) # send message to client
        

def ACK( code, flag, deviceID, time, count):
    if code is 1 and flag is 1: # code of 1 means register ACK, flag of 1 means new device registered
        myReply = str((0, flag, deviceID)) # Tuple to String
        byteReply = str.encode(myReply) # String to Byte
        sock.send(byteReply) # send message to client
    if code is 1 and flag is 2: # code of 1 means register ACK, flag of 2 means device was already registered
        myReply = str((0, flag, deviceID, time, count)) #Tuple to String
        byteReply = str.encode(myReply) #String to Byte
        sock.send(byteReply) # send message to client
    if code is 2: # code of 2 means deregister ACK
        myReply = str((0, deviceID)) # Tuple to String
        byteReply = str.encode(myReply) #S tring to Byte
        sock.send(byteReply) # send message to client
    if code is 3: # code of 3 means MSG ACK
        myReply = str((0, deviceID)) # Tuple to String
        byteReply = str.encode(myReply) # String to Byte
        sock.send(byteReply) # send message to client

#Server Setup Code
portNumber = 9999 # port number for server TCP socket
s = socket(AF_INET, SOCK_STREAM) # initializing new socket
s.bind(('192.168.0.16', portNumber)) # binding server's IP and desired port number to socket
oldStdout = sys.stdout # save old printing setting
logFile1 = open("Activity2.log","w") # open activity log
logFile2 = open("Error2.log","w") # open error log
sys.stdout = logFile1 # change so print prints to desired file instead of console
print("Server side activity", "\n")
startTime = time.time() # gets starting time of the program
deviceTable = [] # initializes table used to store information of registered devices
mailBox = [] # initializes table used to store the mail of clients
s.listen(5) #5 max queued
sock, addr = s.accept() # accepts a connection to the socket
OPEN = True # initial value is true, meaning more packets can be sent by the client to server
while OPEN is True: # OPEN remains true until client quits his connection
    data = sock.recv(1024) # waits to recv data from client
    data = bytes.decode(data) # bytes to str
    data = literal_eval(data) # str to tuple
    if data[0] is 1: # 0 is position of code, code of 1 means register message
        REGISTER(data[1], data[2] , addr[0] , addr[1])
    elif data[0] is 2: # 0 is position of code, code of 1 means deregister message
        DEREGISTER(data[1], data[2])
    elif data[0] is 3: # 0 is position of code, code of 3 means mail message
        MSG( data[1], data[2], data[3], time.time() - startTime )
    elif data[0] is 4: # 0 is position of code, code of 4 means query message
        QUERY( data[1], data[2] )
    elif data[0] is 5: # 0 is position of code, code of 5 means quit message
        OPEN = False
        print("Connected device: ", data[1], " is leaving network", "\n")
    else:
        sys.stdout = logFile2 # switches to printing to error log
        print("malform packet detected from IP: ", addr[0])
        sys.stdout = logFile1 # switches back to printing to activity log
sys.stdout = oldStdout # change back to normal printing
logFile1.close() # close activity log file
logFile2.close() # close error log file
        
