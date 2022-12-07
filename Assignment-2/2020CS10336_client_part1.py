# import chunk
# from http import server
import threading
import socket
import random
import hashlib
import time
import logging
import csv

local_host = "127.0.0.1"
bufferSize = 1028
number_of_clients = 5
threads = []

serverTcpConnectionPort = 49000
server_udp_ports = [ 50000 + i + 1 for i in range(number_of_clients) ]
client_udp_ports = [ 54000 + i + 1 for i in range(number_of_clients) ]
client_tcp_connection_ports = [ 52000 + i + 1 for i in range(number_of_clients) ]
server_tcp_ports = [ 58000 + i + 1 for i in range(number_of_clients) ]

random_requests = False
 
# Create and configure logger
logging.basicConfig(filename="part-1-RTT.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
 
# Creating an object
logger = logging.getLogger()
 
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)
number_of_clients_finished = 0
lock = threading.Lock()
all_RTTs = {}
total_number_of_chunks = 0
def client_func( client_number ):
    global all_RTTs
    global total_number_of_chunks
    global number_of_clients_finished
    clientStartTime = time.time()
    #print(f"Inside client number {client_number}")
    ### create a TCP socket and connect to the server for initial interaction
    TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPClientSocket.connect((local_host, serverTcpConnectionPort))
    ### server first sends the number of chunks
    
    numberOfChunks = int(TCPClientSocket.recv(bufferSize))
    total_number_of_chunks = numberOfChunks
    # logging.info(f"Client Number {client_number} to receive {numberOfChunks} kilobytes")
    
    ### this dict holds all the chunks to be received
    chunks_received = {}
    #### 
    RTT_from_chunkID = {}
    
    ### server sends initial packets and ends this exhange by sending -1 
    while True : 
        ### keep listening for initial packets
        message = TCPClientSocket.recv(1024+4+4) #### receive a packet from the server initial interaction

        if( message == b'-1') : 
            break ### server sends this message to terminate the initial interaction
        elif( message[-2:] == b'-1' ):
            # logging.error(f"COMBINED MESSAGES RECEIVED BY CLIENT {client_number}")
            # logging.info(f"{message}, error in intial transfer for {client_number}")
            message  = message[:-2]
        
        # else:
        chunkNumber = int.from_bytes(message[-8:-4], "big") ### second last four bytes in each message is the packet number
        packetSize = int.from_bytes(message[-4:], "big") ### last 4 bytes is packet size
        # logging.info(f"-- INITIAL TRANSFER FROM SERVER --- {chunkNumber} of size {packetSize} received by client number {client_number} from server")
        chunks_received[chunkNumber] = message[0:packetSize]
    
    TCPClientSocket.close()
    print(f"Time Take to receive all chunks by client {client_number} is {time.time()-clientStartTime} s")
    chunks_not_received = [ x for x in range(1,numberOfChunks+1) if x not in chunks_received ]
    number_of_chunks_received = numberOfChunks - len(chunks_not_received)
    # logging.info(f"Client Number #{client_number} has received {number_of_chunks_received} number of chunks")
    ### we create a TCP socket which listens for server responses of chunks
    TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPClientSocket.bind(("127.0.0.1",  client_tcp_connection_ports[client_number-1]))
    TCPClientSocket.listen(numberOfChunks)
    TCPClientSocket.settimeout(1)
    ### we create a UDP socket to listen for server requests for chunks
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.bind((local_host, client_udp_ports[client_number-1]))
         
    
    def handleServerRequest( UDPClientSocket ) : 
        #### listens to request from servers
        ### this UDP socket will be closed  by the client when it is done and hence we include a try except block to also end this thread
        tempTCPSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        try:
            while True : 
                message, clientAddr = UDPClientSocket.recvfrom(bufferSize)
                chunkRequested = int(message.decode())
                # logging.info(f"SERVER HAS REQUESTED CLIENT {client_number} chunk {chunkRequested}")  
                
                ### send the chunk if the client has it
                if( chunkRequested in chunks_received ) :   
                    chunk_to_be_sent = chunks_received[chunkRequested]
                    message_to_be_sent = chunk_to_be_sent + (chunkRequested).to_bytes(4, 'big')
                    try:
                        tempTCPSocket.send(message_to_be_sent)
                    except:
                        tempTCPSocket.connect( (local_host, server_tcp_ports[client_number-1]))
                        tempTCPSocket.send(message_to_be_sent)
        except:
            print(f"Client Number {client_number} is closing UDP socket to listen for broadcasts")
            tempTCPSocket.send(str(-1).encode())
            tempTCPSocket.close()
        
    while True : 
            try:
                connectionSocket, addr = TCPClientSocket.accept() 
                break
            except:
                pass       

    thread1 = threading.Thread( target=handleServerRequest, args=(UDPClientSocket,))
    thread1.start() #### this thread listens for server requests
    tempUDPClientSocket = UDPClientSocket
    chunksRecieved = 0
    lastTime = time.time()
    printSize = 1000
    if( not random_requests ) : 
        chunks_not_received.sort(reverse=True)
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    total_request_time = 0
    total_packets = 0    
    while( len(chunks_not_received) > 0 ) : 
        if(random_requests):
            i = random.choice(chunks_not_received)
        else:
            i = chunks_not_received[-1] #### request packet from end
        # print( f" -- CLIENT LOOKING FOR MISSING PACKETS -- Client Number {client_number} requests chunk {i} to SERVER")
        packetRequestTime = time.time()
        UDPClientSocket.sendto( (str(i) + "$" + str(client_tcp_connection_ports[client_number-1])).encode(), (local_host, server_udp_ports[client_number-1]))
        while True : 
            try:
                message = connectionSocket.recv(1024+4)
                if( message == b"-1") :
                    ### server sends information that is no longer going to use this socket to send information since client told server that it has received all information  
                    # print( f" client {client_number} has received all chunks and is closing TCP connection") 
                    break
                packetRecieveTime = time.time()
                chunkNumber = int.from_bytes(message[-4:], "big")
                chunks_received[chunkNumber] = message[:-4]
                chunksRecieved += 1
                total_packets += 1
                if( chunksRecieved % printSize == 0 ):
                    print(f"Client Number {client_number} received last {printSize} chunks in {time.time() - lastTime} s")
                    lastTime = time.time()
                if( random_requests == True ):
                    chunks_not_received.remove(chunkNumber)
                else:
                    chunks_not_received.pop()
                RTT_from_chunkID[chunkNumber] = packetRecieveTime - packetRequestTime
                total_request_time += RTT_from_chunkID[chunkNumber]
                # print( f"-- SERVER REPLY TO REQUEST -- client Number {client_number} received chunkNumber {chunkNumber}")     
                # logger.info(f"Client Number {client_number} has {len(chunks_not_received)} remaining chunks")
                break    
            except:
                ## timeout exception called
                print(f"Client Number {client_number} re-requesting chunk number {chunkNumber}")
                UDPClientSocket.sendto( (str(i) + "$" + str(client_tcp_connection_ports[client_number-1])).encode(), (local_host, server_udp_ports[client_number-1]))
        # UDPClientSocket.close()     
    connectionSocket.close()
    UDPClientSocket.close()                     
    print(f"Client {client_number} took {time.time()- clientStartTime} s to recieve all packets")
    
    ### tell server UDP port that client is no longer looking for data 
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.sendto( ("end$" + str(client_tcp_connection_ports[client_number-1])).encode(), (local_host, server_udp_ports[client_number-1]))
    UDPClientSocket.close()
   
    #print(f"Client Number {client_number} has received all packets")
    
    
    lock.acquire()
    number_of_clients_finished += 1
    lock.release()
    while( number_of_clients_finished < number_of_clients ) : 
        ### keep waiting till all clients are finished
        pass

    logging.info(f"Average RTT for all requested packets for Client {client_number} is {total_request_time/total_packets}")
    
    ### this statement will be used to close the UDP socket listening for broadcasts
    tempUDPClientSocket.close()
    fileStartTime = time.time()
    total_file = bytearray(b'')
    for i in range(1,numberOfChunks+1):
        try:
            for b in chunks_received[i]:
                total_file.append(b)
        except:
            print(f"-- ERROR -- client {client_number} does not have chunk {i}")
    total_file = bytes(total_file)
    hash_of_file = hashlib.md5(total_file).hexdigest()
    print(f"Client number {client_number} has file with hash {hash_of_file}")
    
    # print(f"Client number {client_number} is restoring the txt file")
    
    with open(f"{client_number}.txt", "wb") as f : 
        f.write(total_file)    

    fileEndTime  = time.time()
    # print(f"Total time to write file for client {client_number} is {fileEndTime-fileStartTime} s")
    lock.acquire()
    all_RTTs[client_number] = RTT_from_chunkID
    lock.release()

end_threads = []
for i in range(number_of_clients):   
    # for each client we create one thread the client_func handles the process for each client in one thread
    x = threading.Thread(target=client_func, args=(i+1,))
    threads.append(x)
    x.start()
    end_threads.append(x)

for t in end_threads:
    t.join()

### uncomment this code to generate the CSV files with RTT values remember to delete those files before running this code
# f = open('part-1-RTT.csv', 'w', newline="")
# print(total_number_of_chunks) 
# writer = csv.writer(f)
# writer.writerow(["Chunk ID", "Average RTT across clients"])
# for i in range(1,total_number_of_chunks+1):
#     total_time = 0
#     for client_number in range(1,number_of_clients+1):
#         if( i in all_RTTs[client_number]):
#             # print(all_RTTs[client_number][i], end= ",")
#             total_time += all_RTTs[client_number][i]
#         else:
#             # print("-", end=" ")
#             pass
#     print(f"{i},{total_time/(number_of_clients-1)}")
#     writer.writerow([i, total_time/(number_of_clients-1)])
    
# f.close()