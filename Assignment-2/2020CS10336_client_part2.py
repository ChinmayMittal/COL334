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
serverTcpConnectionPort = 50000
threads = []
random_requests = False

client_udp_ports = [ 55000 + i + 1 for i in range(number_of_clients) ]
server_tcp_ports = [ 57000 + i + 1 for i in range(number_of_clients) ]
client_tcp_ports = [ 59000 + i + 1 for i in range(number_of_clients) ]
server_udp_ports = [ 53000 + i + 1 for i in range(number_of_clients) ]

broadCastListenersStarted = 0
clients_completed = 0
lock = threading.Lock()
all_RTTs = {}
total_number_of_chunks = 0
# Create and configure logger
logging.basicConfig(filename="part-2-RTT.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
 
# Creating an object
logger = logging.getLogger()
 
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

def client_func(client_number):
    global broadCastListenersStarted
    global clients_completed
    global all_RTTs
    global total_number_of_chunks
    clientStartTime = time.time()
    ### create a UDP port for the client to listen for inital chunks
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.bind(("127.0.0.1",client_udp_ports[client_number-1])) 
     
    TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPClientSocket.connect((local_host, serverTcpConnectionPort))
    numberOfChunks = int(TCPClientSocket.recv(bufferSize))
    total_number_of_chunks = numberOfChunks
    print(f"Client Number {client_number} to receive {numberOfChunks} kilobytes")    
    TCPClientSocket.close()
   
    ### this dict holds all the chunks to be received
    chunks_received = {} 
    
    RTT_from_chunkID = {}
    
    while True : 
        message, serverUDPInitialAddress = UDPClientSocket.recvfrom(1024+4+4)
        UDPClientSocket.sendto(str("ACK").encode(), serverUDPInitialAddress)
        if( message == b'-1') : 
            break ### server sends this message to terminate the initial interaction
        chunkNumber = int.from_bytes(message[-8:-4], "big") ### second last four bytes in each message is the packet number
        packetSize = int.from_bytes(message[-4:], "big") ### last 4 bytes is packet size
        # print(f"-- INITIAL TRANSFER FROM SERVER --- {chunkNumber} of size {packetSize} received by client number {client_number} from server")
        chunks_received[chunkNumber] = message[0:packetSize]    
    chunks_not_received = [ x for x in range(1,numberOfChunks+1) if x not in chunks_received ]
    number_of_chunks_received = numberOfChunks - len(chunks_not_received)
    
    print(f"Time Take to receive all initial chunks by client {client_number} is {time.time()-clientStartTime} s")
    ### handle closing of initial UDP port on server side
    UDPClientSocket.close()
     
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.bind(("127.0.0.1",client_udp_ports[client_number-1])) 
    UDPClientSocket.settimeout(1)
    def handleServerBroadCast( tcpBroadCastSocket ):  
        tempUDPSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        tempUDPSocket.settimeout(1)       
        while True : 
            connectionSocket, addr = tcpBroadCastSocket.accept()
            message = connectionSocket.recv(bufferSize)
            if( message == b'-1'):
                connectionSocket.close()
                break
            message = message.decode()
            chunkRequested = int(message)
            # print(f"SERVER HAS REQUESTED CLIENT {client_number} chunk {chunkRequested}")  
            if( chunkRequested in chunks_received):
                ### send broadcast response to server
                chunk_to_be_sent = chunks_received[chunkRequested]
                message_to_be_sent = chunk_to_be_sent + (chunkRequested).to_bytes(4, 'big')    
                tempUDPSocket.sendto(message_to_be_sent, (local_host, server_udp_ports[client_number-1]))
                ### listen for acknowledgment from servers or resend on timeout
                acknowledgmentReceived = False
                while( not acknowledgmentReceived ) :
                    try:
                        message, addr = tempUDPSocket.recvfrom(bufferSize)
                        acknowledgmentReceived = True
                    except:
                        tempUDPSocket.sendto(message_to_be_sent, (local_host, server_udp_ports[client_number-1]))
            connectionSocket.close()
        tempUDPSocket.close()
            
            
    
    tcpBroadCastSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    tcpBroadCastSocket.bind((local_host, client_tcp_ports[client_number-1]))
    tcpBroadCastSocket.listen(numberOfChunks)
    
    broadCastThread = threading.Thread(target=handleServerBroadCast, args =(tcpBroadCastSocket,))
    broadCastThread.start()
    
    lock.acquire()
    broadCastListenersStarted += 1
    lock.release()
    
    while(broadCastListenersStarted < number_of_clients):
        pass
        
    if( not random_requests ) : 
        chunks_not_received.sort(reverse=True)
        
    total_request_time = 0
    total_packets = 0
    printSize = 10 if( numberOfChunks < 1000) else 1000
    lastTime = time.time()
    
    tcpSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    tcpSocket.connect((local_host, server_tcp_ports[client_number-1]))
    while( len(chunks_not_received) > 0 ) : 
        if(random_requests):
            i = random.choice(chunks_not_received)
        else:
            i = chunks_not_received[-1] #### request packet from end
        # print( f" -- CLIENT LOOKING FOR MISSING PACKETS -- Client Number {client_number} requests chunk {i} to SERVER")
        packetRequestTime = time.time()
        tcpSocket.send((str(i) + '$' + str(client_udp_ports[client_number-1])).encode()) 
        while True : 
            message, serverAddress = UDPClientSocket.recvfrom(1024+4)
            UDPClientSocket.sendto(str("ACK").encode(), serverAddress)
            chunkNumber = int.from_bytes(message[-4:], "big")
            chunks_received[chunkNumber] = message[:-4]
            if( chunkNumber not in RTT_from_chunkID ):
                total_packets += 1
                RTT_from_chunkID[chunkNumber] = ( time.time() - packetRequestTime ) 
                total_request_time += RTT_from_chunkID[chunkNumber]
                
                if( total_packets % printSize == 0 ):
                    # print(f"Time Take to receive last {printSize} by client {client_number} is {time.time()-lastTime} s")
                    lastTime = time.time()
            if( random_requests == True ):
                    chunks_not_received.remove(chunkNumber)
            else:
                    chunks_not_received.pop() 
            break 

        # print( f"-- SERVER REPLY TO REQUEST -- client Number {client_number} received chunkNumber {chunkNumber}")
    
    lock.acquire()
    clients_completed += 1
    lock.release()
    print(f"Client {client_number} took {time.time()- clientStartTime} s to recieve all packets")
    while( clients_completed < number_of_clients ) :
        pass 
    ### close server port listening for requests which closes client port listening for requests
    tcpSocket.send((str("end") + '$' + str(client_tcp_ports[client_number-1])).encode()) 
    tcpSocket.close()   
    broadCastThread.join()
    ### close server port listening for broadcast responses
    tempUDPsocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    tempUDPsocket.sendto(b'-1', (local_host, server_udp_ports[client_number-1]))
    ### handle acknowledgment
    tempUDPsocket.close()
    UDPClientSocket.close()

    logging.info(f"Average RTT for all requested packets for Client {client_number} is {total_request_time/total_packets}")    
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
    
    print(f"Client number {client_number} is restoring the txt file")
    
    with open(f"{client_number}.txt", "wb") as f : 
        f.write(total_file)        

    lock.acquire()
    all_RTTs[client_number] = RTT_from_chunkID
    lock.release()                   
            
                     
end_threads = []
for i in range(number_of_clients):
 
    x = threading.Thread(target=client_func, args=(i+1,))
    threads.append(x)
    x.start()    
    end_threads.append(x)

for t in end_threads:
    t.join()
    
### un-comment this code to save a CSV file with RTTs ensure that file is already not present
# f = open('part-2-RTT.csv', 'w', newline="")
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