import socket
from chunks import *

local_host = "127.0.0.1"
serverPort = 49000

TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
TCPServerSocket.bind((local_host,  serverPort))
TCPServerSocket.listen(1)


while True:
    connectionSocket, addr = TCPServerSocket.accept()
    chunkID = connectionSocket.recv(1024).decode()
    chunkID = int(chunkID)
    if(chunkID == 11):
        break
    else:
        chunk, hashOfChunk = get_chunk(chunkID)
        messsage_to_be_sent = (chunk + "$" + hashOfChunk).encode()
        connectionSocket.send(messsage_to_be_sent)

