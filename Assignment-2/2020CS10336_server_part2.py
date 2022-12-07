import socket
import hashlib
import random
import math
from sqlite3 import connect
import threading
from LRU import LRUCache
import time

startTime = time.time()

lock = threading.Lock()

simulationStartTime = time.time()
number_of_clients = 5
bufferSize = 2048
local_host = "127.0.0.1"
cache_capacity = number_of_clients ### default cache setting
# cache_capacity = 1


file_to_be_shared =  "A2_small_file.txt"
# file_to_be_shared = "A2_large_file.txt"
byte_array = None ### stores the txt file as bytes
with open(file_to_be_shared, "rb") as f : 
    byte_array = f.read()

chunk_size = 1024
number_of_chunks = math.ceil( len(byte_array) / chunk_size )  ### divide file into 1KB chunks

### inital welcoming TCP soceket
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
TCPServerSocket.bind((local_host,  50000))
TCPServerSocket.listen(number_of_clients)

client_udp_ports = [ 55000 + i + 1 for i in range(number_of_clients) ]
server_tcp_ports = [ 57000 + i + 1 for i in range(number_of_clients) ]
client_tcp_ports = [ 59000 + i + 1 for i in range(number_of_clients) ]
server_udp_ports = [ 53000 + i + 1 for i in range(number_of_clients) ]

cache = LRUCache( capacity=cache_capacity)

def handleInitialReq(connectionSocket, client_number):
    msgFromServer = str(number_of_chunks)
    bytesToSend   = str.encode(msgFromServer)
    connectionSocket.send( bytesToSend )
    connectionSocket.close()
    ### create a UDP socket to send data to the clients
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.settimeout(1)
    for chunkNumber in range( client_number,number_of_chunks+1,number_of_clients) : 
        ### round - robin allocation of initial packets
        chunk_to_be_sent = byte_array[(chunkNumber-1)*1024 : min(chunkNumber*1024,len(byte_array))]
        len_of_chunk = len(chunk_to_be_sent)
        chunk_to_be_sent += b"0" * ( chunk_size - len_of_chunk) #### null pad packet size to fixed packet size
        message_to_be_sent = chunk_to_be_sent + (chunkNumber).to_bytes(4, 'big') + len_of_chunk.to_bytes(4,"big")
        test = int.from_bytes(message_to_be_sent[-8:-4],"big" )
        # print(f" -- INITIAL TRANSFER FROM SERVER TO CLIENT --- {test} sent to client number {client_number}")
        UDPServerSocket.sendto(  message_to_be_sent, (local_host, client_udp_ports[client_number-1] ))
        acknowledgmentReceived = False 
        while( not acknowledgmentReceived ) :
            try:
                acknowledgment, clientAddr = UDPServerSocket.recvfrom(bufferSize)
                acknowledgmentReceived = True
                # print(f"{acknowledgment.decode()} received from client {client_number} for chunk {chunkNumber} ")
            except:
                UDPServerSocket.sendto(  message_to_be_sent, (local_host, client_udp_ports[client_number-1] ))
                
    UDPServerSocket.sendto(str(-1).encode(), (local_host, client_udp_ports[client_number-1] ))
    acknowledgmentReceived = False
    while( not acknowledgmentReceived ):
        try:
            acknowledgment, clientAddr = UDPServerSocket.recvfrom(bufferSize)
            acknowledgmentReceived = True
            print(f"{acknowledgment.decode()} received from client {client_number} for sending all packets through INITIAL UDP connection ")
        except:
            UDPServerSocket.sendto(str(-1).encode(), (local_host, client_udp_ports[client_number-1] ))
    UDPServerSocket.close()

def handleClientResponse( udpSocket ):
    ### listens to broadcast response from clients
    global cache 
    while True : 
        message, address = udpSocket.recvfrom(bufferSize)
        if( message == b'-1'):
            udpSocket.close()
            break
        chunkNumber = int.from_bytes(message[-4:], "big")
        chunk = message[:-4]
        # print(f"client {address} sent {chunkNumber} to server")
        ### send acknowledgment
        udpSocket.sendto(("ACK").encode(), address)
        ####
        # lock.acquire()
        if( not cache.isPresent(chunkNumber=chunkNumber)):
            cache.insert(chunkNumber, chunk)                
        # lock.release()
    
def handleClientRequest( tcpSocket ) :
    global cache
    global connection_sockets
    while True:
        connectionSocket, addr = tcpSocket.accept()    
        break    
    while True : 
        # connectionSocket, addr = tcpSocket.accept()   
        message = connectionSocket.recv(bufferSize)
        message = message.decode().split("$")
        if( message[0] == "end"):
            temp2TcpSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            temp2TcpSocket.connect((local_host, int(message[1]))) ### message[1] has client_tcp_port
            temp2TcpSocket.send(b'-1')
            temp2TcpSocket.close()
            connectionSocket.close()
            break
        chunkRequested = int(message[0])
        clientUDPPort = int(message[1])
        # print( f"--CLIENT REQUEST TO SERVER --- {clientUDPPort} requested {chunkRequested}")
        tempUDPSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # tempUDPSocket.settimeout(1)
        #### find chunk
        # lock.acquire()
        if( cache.get(chunkNumber=chunkRequested) == -1 ) : 
            #### request chunk to all clients (BROADCAST)
            for i in range(1,number_of_clients+1):
                tempTcpSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                tempTcpSocket.connect((local_host, client_tcp_ports[i-1]))
                tempTcpSocket.send(str(chunkRequested).encode())
                tempTcpSocket.close()
        else:
            pass     
        # lock.release()
        #####
        while( not cache.isPresent(chunkNumber=chunkRequested)):
            pass
            
        chunk_to_be_sent = cache.get(chunkNumber=chunkRequested)
        chunk_to_be_sent  = chunk_to_be_sent + (chunkRequested).to_bytes(4, 'big')
        tempUDPSocket.sendto( chunk_to_be_sent, (local_host, clientUDPPort))
        acknowledgmentReceived = False
        while( not acknowledgmentReceived ) : 
            try:
                message, addr = tempUDPSocket.recvfrom(bufferSize)
                acknowledgmentReceived = True
            except:
                tempUDPSocket.sendto( chunk_to_be_sent, (local_host, clientUDPPort))
        tempUDPSocket.close()
        # connectionSocket.close()
        
        
start_threads = []
end_threads = []
client_number = 1
while True:
    ### accept initial connections
    connectionSocket, addr = TCPServerSocket.accept()
    thread =  threading.Thread(target=handleInitialReq, args=(connectionSocket,client_number))
    thread.start()
    start_threads.append(thread)
    client_number += 1
    
    if( client_number > number_of_clients ) :
        break
for i in range(number_of_clients):
    start_threads[i].join()
        
for client_number in range(number_of_clients):     

    
    tcpSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    tcpSocket.bind((local_host,  server_tcp_ports[client_number-1]))
    tcpSocket.listen(number_of_chunks)    
    thread2 = threading.Thread(target=handleClientRequest, args=(tcpSocket,))
    thread2.start()
    
    udpSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udpSocket.bind((local_host, server_udp_ports[client_number-1]))
    
    thread3 = threading.Thread(target=handleClientResponse, args =(udpSocket,))
    thread3.start()
    end_threads.append(thread3)
    

for t in end_threads:
    t.join()
    
endTime = time.time()
print(f"Simulation Time: {endTime-startTime} s")