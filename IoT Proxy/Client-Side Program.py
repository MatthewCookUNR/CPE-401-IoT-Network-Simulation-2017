from socket import socket, AF_INET, SOCK_STREAM
from uuid import getnode
from ast import literal_eval
import time
import sys

#Registers device onto the server using device's id and MAC address
def REGISTER( deviceID ):
    print("Registering my IoT device")
    myMAC = getnode() # gets MAC address of device in a form of 48-bit integer
    myMAC = hex(myMAC)
    myMAC = myMAC[2:] # removes '0x' from the hexadecimal number
    myMAC = ':'.join(format(s, '02x') for s in bytes.fromhex(myMAC)) #seperates hexadecimal into MAC address form (borrowed from stackoverflow)
    print('My device ID sent to server: ', deviceID,' My MAC address sent to server: ', myMAC )
    myMessage = ( 1, deviceID, myMAC ) # Info needed to register along with code identifier that packet is for registration
    myMessage = str(myMessage)
    myMessage = str.encode(myMessage)
    s.send(myMessage) #send message to server
    data = s.recv(1024) # waits for response from server
    data = bytes.decode(data)
    data = literal_eval(data)
    print ("Server reply to client: ", data)
    messageType = data[0] # First member of tuple is type( 0 for ACK, 1 for NACK )
    flag = data[1] # Second member of tuple is flag of message
    if messageType is 0:  # message is ACK
        if flag is 1: # successfully registered
            print("Successful registration of device", "\n")
        elif flag is 2: # client has already been registered
            print("Device was already registered at time of ", data[3])
            print("You have ", data[4], " new messages", "\n")
        else:
            sys.stdout = log_file2 # switch to logging to error.log
            print("Error: malformed packet detected during registration", "\n")
            sys.stdout = log_file1 # switch back to logging to activity.log
    elif messageType is 1: # message is NACK
        print("Device failed to register")
        print("Current registered device with your info:")
        print("DeviceID: ", data[1], " MAC: ", data[2], "\n")
    else: # malformed packet recieved
        sys.stdout = logFile2 # switch to logging to error.log
        print("Error: malformed packet detected during registration", "\n")
        sys.stdout = logFile1 # switch back to logging to activity.log

#Deregisters device from server's stored registry
def DEREGISTER(deviceID):
    print("Deregistering my IoT device")
    myMAC = getnode()# gets MAC address of device in a form of 48-bit integer
    myMAC = hex(myMAC)
    myMAC = myMAC[2:] # removes '0x' from the hexadecimal number
    myMAC = ':'.join(format(s, '02x') for s in bytes.fromhex(myMAC)) #seperates hexadecimal into MAC address form (borrowed from stackoverflow)
    print('My device ID sent to server: ', deviceID,' My MAC address sent to server: ', myMAC )
    myMessage = (2, deviceID, myMAC) # Info needed to deregister along with code identifier that packet is for deregistration
    myMessage = str(myMessage)
    myMessage = str.encode(myMessage)
    s.send(myMessage) #send message to server
    data = s.recv(1024) # waits for response from server
    data = bytes.decode(data)
    data = literal_eval(data)
    print ("Server reply to client:", data)
    messageType = data[0] # first member of tuple is type( 0 for ACK, 1 for NACK )
    if messageType is 0: # message is ACK
        print("Device was successfully deregistered or wasn't registered", "\n")
    elif messageType is 1: # message is NACK
        print("Device was not deregistered", "\n")
    else: # malformed packet recieved
        sys.stdout = logFile2 # switch to logging to error.log
        print("Error: malformed packet detected during de-registration", "\n")
        sys.stdout = logFile1 # switch back to logging to activity.log

#Client leaves the proxy network
def QUIT(userID):
    print("IoT device leaving the system")
    myMessage = (5, userID) # info needed needed to tell the server it is quitting
    myMessage = str(myMessage)
    myMessage = str.encode(myMessage)
    s.send(myMessage) # send packet to server
    s.close() # close connection with server
    print("IoT device closed connection", "\n")

#Sends a message as mail from one client to another that is stored by server
def MSG( fromID, toID, message ):
    print("Sending message: ",message," to: ", toID, " from: ", fromID)
    myMessage = (3, fromID, toID, message) #info needed to send a message from one device to another
    myMessage = str(myMessage)
    myMessage = str.encode(myMessage)
    s.send(myMessage) # send message to server
    data = s.recv(1024) # waits for response from server
    data = bytes.decode(data)
    data = literal_eval(data)
    print ("Server reply to client:", data)
    messageType = data[0] # first member of tuple is type( 0 for ACK, 1 for NACK )
    if messageType is 0: # message is ACK
        print("MSG was transmitted successfully", "\n")
    elif messageType is 1: # message is NACK
        print("MSG failed, recieving deviceID was not registered with server", "\n")
    else: # malformed packet recieved
        sys.stdout = logFile2 # switch to logging to error.log
        print("Error: malformed packet detected during message sending", "\n")
        sys.stdout = logFile1 # switch back to logging to activity.log

#Gets information stored in server for the client device
def QUERY( code, deviceID ):
    if code is 1: # device is querying server for a device's information
        print("IoT device querying server for a device, specifically device ID: ", deviceID)
        myMessage = (4,1,deviceID) #info needed to query for another device's info
        myMessage = str(myMessage)
        myMessage = str.encode(myMessage)
        s.send(myMessage) # send message to server
        data = s.recv(1024) # waits for response from server
        data = bytes.decode(data)
        data = literal_eval(data)
        messageType = data[0] # first member of tuple is type( 0 for ACK, 1 for NACK )
        print ("Server reply to client:", data)
        if messageType is 0: # message is ACK
            print("Found the queried device info, IP: ", data[1], " port: ", data[2], "\n")
        elif messageType is 1:  # message is NACK
            print("Queried device not found in server", "\n")
        else: # malformed packet recieved
            sys.stdout = logFile2 # switch to logging to error.log
            print("Error: malformed packet detected during device ID query", "\n")
            sys.stdout = logFile1 # switch back to logging to activity.log
    if code is 2: # device is querying server for its mail in server's mailbox
        myMessage = (4,2,userID) # info needed to query server for mail
        myMessage = str(myMessage)
        myMessage = str.encode(myMessage)
        s.send(myMessage)
        data = s.recv(1024) # waits for response from server
        data = bytes.decode(data)
        data = literal_eval(data)
        messageType = data[0]
        print ("Server reply to client:", data)
        if messageType is 0: # message is ACK
            print("Mail Recieved Successfully, list of mail: ", data[1], "\n")
            s.send(b'0') # sends a message to let server know mail was recieved
        elif messageType is 1: # message is NACK
            print("Mail not recieved successfully", "\n")
        else: # malformed packet recieved
            sys.stdout = logFile2 # switch to logging to error.log
            print("Error: malformed packet detected during mail query", "\n")
            sys.stdout = logFile1 # switch back to logging to activity.log
    
#Client Setup/Run Code
(serverIP, serverPort) = ('192.168.56.1', 9999)
userID = "ClientTop"
oldStdout = sys.stdout 
logFile1 = open("Activity1.log","w") # open activity log
logFile2 = open("Error1.log","w") # open error log
sys.stdout = logFile1 # makes it so print function prints to log file
print("Client side activity", "\n")
s = socket(AF_INET, SOCK_STREAM) # create TCP socket
s.connect((serverIP, serverPort)) # connect to server using socket
print("Client Connects")
MSG(userID, userID, "Message1")
REGISTER(userID)
MSG(userID, userID, "Message1")
MSG(userID, userID, "Message2")
REGISTER(userID)
QUERY(1, "ClientTop")
QUERY(1, "ClientTop2")
QUERY(2, userID)
DEREGISTER(userID)
DEREGISTER(userID)
QUIT(userID)
sys.stdout = oldStdout
logFile1.close()
logFile2.close()
    
