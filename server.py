from ctypes import addressof
from operator import length_hint
import os
import shutil
import sys
import socket
import tempfile
from time import process_time_ns
from traceback import print_tb

# port and cache
PORT = 8080

#create the welcome socket and bind it to the port
welcomeSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
welcomeSocket.bind(('localhost', PORT))
os.mkdir('cache')
print("[*] Listening on localhost:%d\n" % (PORT))
welcomeSocket.listen(1)                 # listen for one connection
while(True):
    try:
        print("WEB PROXY SERVER IS LISTENING")
        # accept and create a socket for the connection
        clientSocket, address = welcomeSocket.accept()
        print("[*] Accepted connection from: %s:%d\n" % (address[0], address[1]))
        # receive the clientMessage
        clientMessage = clientSocket.recv(1024).decode()
        print("[*] Message Recieved from Client:\n%s[*] End of Message\n\n" % (clientMessage))

        # Parse the clientMessage into its separate parts
        print("[*] Parsing clientMessage Header: ")
        rows = clientMessage.splitlines(True)    # split the clientMessage into lines
        parts = rows[0].split(' ')     # split the first line into parts
        method = parts[0]               # get the method
        version = parts[2]              # get the http version
        url = parts[1][1:]              # get the url
        x = len(url.split('/'))
        host = url.split('/')[0]        # get the host
        if x > 1: 
            path = url.split("/",1)[1]
        else: 
            path = ''     # get the path
            redirect = True
        filename = url.split('/')[-1]   # get the filename
        print("[*] Method: %s, Destination: %s, Version: %s" % (method, url, version))

        if method == "GET":
           
            # check if the file is in the cache
            if not os.path.exists('cache/' + filename):
                print("\n[*] File not in cache")
                # if not, get the file from the server
                serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                serverSocket.connect((host, 80))

                print("Hostname: %s\nURL: %s\nFilename: %s\n" % (host, path, filename))

                # send the clientMessage to the server
                rows[0] = ("GET /%s HTTP/1.1\r\n" % (path))
                rows[1] = ("Host: %s\r\n" % (host))
                serverSocket.send((''.join(rows)).encode())
                print("[*] Message Sent to Server:\n%s[*] End of Message\n\n" % (''.join(rows)))
                

                # receive the response from the server
                response = serverSocket.recv(2048).decode()
                # parse the response
                header = response.split("\r\n\r\n",1)[0]
                lines = header.splitlines()    # split the clientMessage into lines
                
                # header 
                print("[*] Response Recieved from Server: \n%s\n[*] End of Header\n\n" % ('\n'.join(lines)))

                # get components to write a response to the client
                status = lines[0].split(' ', 1)

                # write the body to the cache
                if status[1] == "200 OK":
                    lines  = response.splitlines()
                    tempfile = open('cache/' + filename, 'w')   # add the file to the cache
                    for i in lines:
                        tempfile.write(i + '\r\n')
                    tempfile.close()
                elif status[1] == "403 Forbidden":
                    status[1] = "302 Found"
                serverSocket.close()
                # send the response to the client
                if(redirect == True):
                    clientSocket.send(("HTTP/1.1 302 Found\nLocation: http://" + host + "/" + path + "\n\n").encode())
                    print("[*] Redirecting to: http://" + host + "/" + path)
                else:
                    bytesResponse = ('\r\n'.join(lines)).encode()
                    clientSocket.send(bytesResponse)
                proxyResponse = "\nHTTP/1.1 %s\nContent-Type: text/html; charset =UTF-8\n" % (status[1])
                print("[*] Response header from Proxy to Client: %s\n[*] End of Header\n\n" % (proxyResponse)) 
                     
            # if the file is in the cache
            else:
                print("\n[*] File in cache\t cache/%s\n" % (filename))
                file = open('cache/' + filename, 'r')


                # parse the response
                lines = file.readlines()    # split into lines
                

                # send the response to the client
                

                byteResponse = str.encode(''.join(lines))
                clientSocket.send(byteResponse)
                clientResponse = clientSocket.recv(1024).decode()
                print("[*] Response from Proxy to Client: \n%s[*] End of Response\n\n" % ('\n'.join(lines)))

        # if the method is not GET
        else:
            serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverSocket.connect((host, 80))
            
            # send the clientMessage to the server
            message = ("GET /%s HTTP/1.1\r\nHost: %s\r\n\r\n" % (path, host))
            serverSocket.send(message.encode())
            originalMessage = serverSocket.recv(1024).decode()
            originalMessage = originalMessage.splitlines()
            print("[*] Response header from original server: \n%s\n[*] End of Response\n\n" % (originalMessage[0:8]))

            # get components to write a response to the client
            status = originalMessage[0].split(' ', 1)
            contentType = originalMessage[7]
            print("[*] Status: %s\t %s\n" % (status[1], contentType))
            clientSocket.send(("HTTP/1.1 %s\n%s\n" % (status[1], contentType)).encode())


    except KeyboardInterrupt:
        print("[*] Shutting down the server...")
        welcomeSocket.close()
        clientSocket.close()
        shutil.rmtree('cache')
        sys.exit(0)
    except Exception as e:
        print("[*] Exception: %s" % (e))
        continue
