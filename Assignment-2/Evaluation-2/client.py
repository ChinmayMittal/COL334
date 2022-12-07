import socket
from chunks import get_hash

local_host = "127.0.0.1"
serverPort = 49000
file_to_be_writen = ""
f = open("output.txt", "w")   
for i in range(1,12):
    chunk_ID = i

    if( i == 11):
        TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        TCPClientSocket.connect((local_host, serverPort))
        TCPClientSocket.send(str(i).encode())
        TCPClientSocket.close()
        break
    

    
    corrupted = True
    while( corrupted):
        TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        TCPClientSocket.connect((local_host, serverPort))
        TCPClientSocket.send(str(i).encode())
        message_received = TCPClientSocket.recv(1024).decode().split("$")
        chunkReceived, hashReceived = message_received[0], message_received[1]
        if( get_hash(chunkReceived) == hashReceived ):
            corrupted = False
            # print(chunkReceived)
            file_to_be_writen += chunkReceived
        else:
            print(f"Corrupted re-requesting {i}")    
        TCPClientSocket.close()        
    
f.write(file_to_be_writen)
f.close()