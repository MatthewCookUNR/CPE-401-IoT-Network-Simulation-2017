# Project Details
The project was completed in 3 stages. Each stage built off of the previous to create the final finished project.

### Stage 1: IoT Proxy
A simple proxy is created to allow IoT devices to communicate with a server. A pair of programs were created (client and server). All communications happen through the server. Clients establish a TCP connection to interact with the server.

Proxy's Features:
- REGISTER - registers device in server using user given name and device MAC address
- DEREGISTER - deregisters device in server using user given name and device MAC address
- MSG - Text mail sent by client devices to another that is saved in the server
- ACK - message telling client that message and/or function worked properly
- NACK - message telling client that message and/or function received an error
- QUERY - queries server for information such as a registered device or its stored mail
- QUIT - signals to server that client is leaving the network

### Stage 2: IoT Interaction
The IoT proxy is upgraded with the capability of allowing multiple IoT devices to communicate with the server simultaneously. The server uses multithreading and a mutex locks to achieve synchronization.


### Stage 3: IoT Cloud Interaction
The IoT proxy is given the ability to append files onto a cloud using a shared folder on Dropbox. Client devices get access to the cloud through the server.
