from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from uuid import getnode
from ast import literal_eval
import time
import sys
from threading import Thread
from threading import Lock
from threading import Condition
import dropbox

class iotThread(Thread):
    def __init__(self, number, myData, address):
        self.data = myData
        self.destAddr = address
        Thread.__init__(self, name = "Thread " + str(number))
        print (self.getName() + " has been initialized\n")
    def run(self):
        print("no")

def getCloudAccess(deviceID):
    print("Getting access to cloud")
    myMessage = (6, deviceID)
    myMessage = str(myMessage)
    myMessage = str.encode(myMessage)
    s.send(myMessage)
    data = s.recv(1024)
    data = bytes.decode(data)
    print("Access Token: ", data)
    accessToken.append(data)
    
def AppendDataToCloud():
    dataFileName = input("Enter the name of the file being sent to Dropbox: ").strip()
    dataFile = open(dataFileName,'rb')
    response = client.put_file(dataFileName, dataFile)
    
def REGISTER( deviceID ):
    print("Registering my IoT device")
    myMAC = getnode() # gets MAC address of device in a form of 48-bit integer
    myMAC = hex(myMAC) # conversion of 48-bit integer representation to hexadecimal
    myMAC = myMAC[2:] # removes '0x' from the hexadecimal number
    myMAC = ':'.join(format(s, '02x') for s in bytes.fromhex(myMAC)) #seperates hexadecimal into MAC address form (borrowed from stackoverflow)
    print('My device ID sent to server: ', deviceID,' My MAC address sent to server: ', myMAC )
    myMessage = ( 1, deviceID, myMAC ) # Info needed to register along with code identifier that packet is for registration
    myMessage = str(myMessage) # converts message from a tuple to a string
    myMessage = str.encode(myMessage) # converts message from a string to byte message
    s.send(myMessage) #send message to server
    data = s.recv(1024) # waits for response from server
    data = bytes.decode(data) # decodes byte message to a string
    data = literal_eval(data) # converts string back to a tuple
    print ("Server reply to client: ", data)
    messageType = data[0] # First member of tuple is type( 0 for ACK, 1 for NACK )
    flag = data[1] # Second member of tuple is flag of message
    if messageType is 0: # messageType of 0 means that recieved message is a ACK
        if flag is 1: # flag of 1 means recieved ACK is telling client they successfully registered
            print("Successful registration of device", "\n")
        elif flag is 2: # flag of 2 means recieved ACK is telling client that have already been registered
            print("Device was already registered at time of ", data[3])
            print("You have ", data[4], " new messages", "\n")
        else:
            sys.stdout = logFile2 # switch to logging to error.log
            print("Error: malformed packet detected during registration", "\n")
            sys.stdout = logFile1 # switch back to logging to activity.log
    elif messageType is 1: # messageType of 1 means that recieved message is a NACK
        print("Device failed to register")
        print("Current registered device with your info:")
        print("DeviceID: ", data[1], " MAC: ", data[2], "\n")
    else: # malformed packet recieved
        sys.stdout = logFile2 # switch to logging to error.log
        print("Error: malformed packet detected during registration", "\n")
        sys.stdout = logFile1 # switch back to logging to activity.log
    
def DEREGISTER(deviceID):
    print("Deregistering my IoT device")
    myMAC = getnode()# gets MAC address of device in a form of 48-bit integer
    myMAC = hex(myMAC)# conversion of 48-bit integer representation to hexadecimal
    myMAC = myMAC[2:] # removes '0x' from the hexadecimal number
    myMAC = ':'.join(format(s, '02x') for s in bytes.fromhex(myMAC)) #seperates hexadecimal into MAC address form (borrowed from stackoverflow)
    print('My device ID sent to server: ', deviceID,' My MAC address sent to server: ', myMAC )
    myMessage = (2, deviceID, myMAC) # Info needed to deregister along with code identifier that packet is for deregistration
    myMessage = str(myMessage) # converts message from a tuple to a string
    myMessage = str.encode(myMessage) # converts message from a string to byte message
    s.send(myMessage) #send message to server
    data = s.recv(1024) # waits for response from server
    data = bytes.decode(data) # decodes byte message to a string
    data = literal_eval(data) # converts string back to a tuple
    print ("Server reply to client:", data)
    messageType = data[0] # first member of tuple is type( 0 for ACK, 1 for NACK )
    if messageType is 0: # messageType of 0 means that recieved message is a ACK
        print("Device was successfully deregistered or wasn't registered", "\n")
    elif messageType is 1: # messageType of 1 means that recieved message is a NACK
        print("Device was registered with different info, failed", "\n")
    else: # malformed packet recieved
        sys.stdout = logFile2 # switch to logging to error.log
        print("Error: malformed packet detected during de-registration", "\n")
        sys.stdout = logFile1 # switch back to logging to activity.log

def QUIT(userID):
    print("IoT device leaving the system")
    myMessage = (5, userID) # info needed needed to tell the server it is quitting
    myMessage = str(myMessage) # converts message from a tuple to a string
    myMessage = str.encode(myMessage) # converts message from a string to byte message
    s.send(myMessage) # send packet to server
    s.close() # close connection with server\
    clientOn = False
    print("IoT device closed connection", "\n")

def MSG( fromID, toID, message ):
    print("Sending message: ",message," to: ", toID, " from: ", fromID)
    myMessage = (3, fromID, toID, message) #info needed to send a message from one device to another
    myMessage = str(myMessage) #converts message from a tuple to a string
    myMessage = str.encode(myMessage) # converts message from a string to byte message
    s.send(myMessage) # send message to server
    data = s.recv(1024) # waits for response from server
    data = bytes.decode(data) #decodes byte message to a string
    data = literal_eval(data) #converts string back to a tuple
    print ("Server reply to client:", data)
    messageType = data[0] # first member of tuple is type( 0 for ACK, 1 for NACK )
    if messageType is 0: # messageType of 0 means that recieved message is a ACK
        print("MSG was transmitted successfully", "\n")
    elif messageType is 1: # messageType of 1 means that recieved message is a DACK
        print("MSG failed, recieving deviceID was not registered with server", "\n")
    else: # malformed packet recieved
        sys.stdout = logFile2 # switch to logging to error.log
        print("Error: malformed packet detected during message sending", "\n")
        sys.stdout = logFile1 # switch back to logging to activity.log
    
def QUERY( code, deviceID ):
    if code is 1: # device is querying server for a device's information
        print("IoT device querying server for a device, specifically device ID: ", deviceID)
        myMessage = (4,1,deviceID) #info needed to query for another device's info
        myMessage = str(myMessage) #converts message from a tuple to a string
        myMessage = str.encode(myMessage) # converts message from a string to byte message
        s.send(myMessage) # send message to server
        data = s.recv(1024) # waits for response from server
        data = bytes.decode(data) #decodes byte message to a string
        data = literal_eval(data) #converts string back to a tuple
        messageType = data[0] # first member of tuple is type( 0 for ACK, 1 for NACK )
        print ("Server reply to client:", data)
        if messageType is 0: # messageType of 0 means that recieved message is a ACK
            print("Found the queried device info, IP: ", data[1], " port: ", data[2], "\n")
        elif messageType is 1: # messageType of 1 means that recieved message is a DACK
            print("Queried device not found in server", "\n")
        else: # malformed packet recieved
            sys.stdout = logFile2 # switch to logging to error.log
            print("Error: malformed packet detected during device ID query", "\n")
            sys.stdout = logFile1 # switch back to logging to activity.log
    if code is 2: # device is querying server for its mail in server's mailbox
        myMessage = (4,2,userID) # info needed to query server for mail
        myMessage = str(myMessage) # converts message from a tuple to a string
        myMessage = str.encode(myMessage) # converts message from a string to byte message
        s.send(myMessage)
        data = s.recv(1024) # waits for response from server
        data = bytes.decode(data) # decodes byte message to a string
        data = literal_eval(data) # converts string back to a tuple
        messageType = data[0]
        print ("Server reply to client:", data)
        if messageType is 0: # messageType of 0 means that recieved message is a ACK
            print("Mail Recieved Successfully, list of mail: ", data[1], "\n")
            s.send(b'0') # sends a message to let server know mail was recieved
        elif messageType is 1: # messageType of 1 means that recieved message is a DACK
            print("Mail not recieved successfully", "\n")
        else: # malformed packet recieved
            sys.stdout = logFile2 # switch to logging to error.log
            print("Error: malformed packet detected during mail query", "\n")
            sys.stdout = logFile1 # switch back to logging to activity.log

#def DATA( source_ID, dataType, resultFile):
#    dataFile = open(resultFile,"r")
#    allData = (dataFile.readlines())
#    for index in range(len(allData)):
#        currentLine = dataFile[index]
#        currentLine = str.encode(currentLine)
#        sendTo(currentLine, server)
#        reply, addr = s2.recvfrom(1024)
#        reply = bytes.decode(reply)
#        reply = literal_eval(data)
#        if data[0] is not 0:
#            print("Data not recieved correctly")
#            return   
#    dataFile.close()

#Client Setup/Run Code
(serverIP, serverPort) = ('192.168.0.16', 9999)
userID = "MacTop"
oldStdout = sys.stdout 
logFile1 = open("Activity1.log","w") # open activity log
logFile2 = open("Error1.log","w") # open error log
#sys.stdout = logFile1 # makes it so print function prints to log file
print("Client side activity", "\n")
s = socket(AF_INET, SOCK_STREAM) # create TCP socket
s2 = socket(AF_INET, SOCK_DGRAM)
s2.bind(('192.168.0.16', 9999))
server = ('192.168.56.1', 9999)
threadNumber = 0
threadList = []
accessToken = []
#clientOn = True
#DATA( "MacTop", "ping", "PingData.txt")
s.connect((serverIP, serverPort)) # connect to server using socket
getCloudAccess(userID)
client = dropbox.client.DropboxClient(accessToken[0])
print ('linked account: ', client.account_info())
print("Client Connects")
#MSG(userID, "ClientTop", "MacMess1")
REGISTER(userID)
#MSG(userID, "ClientTop", "MacMess1")
AppendDataToCloud()
#MSG(userID, "ClientTop", "MacMess2")
#REGISTER(userID)
#QUERY(1, "ClientTop")
#QUERY(1, "MacTop")
#QUERY(2, userID)
#DEREGISTER(userID)
#DEREGISTER(userID)
#while clientOn is True:
#    print("Trying to get data")
#    data, addr = s2.recvfrom(1024)
#    threadNumber = threadNumber+1
#    threadList.append(iotThread(threadNumber, data, addr))
#    threadList[threadNumber-1].start()
QUIT(userID)
sys.stdout = oldStdout
logFile1.close()
logFile2.close()
    
