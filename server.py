import sys
import signal
import socket

# constants host and port
PORT = 8080


welcomeSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
welcomeSocket.bind(('0.0.0.0', PORT))
print("[*] Listening on 0.0.0.0:%d" % (PORT))
welcomeSocket.listen(5)
while(True):
    try:
        (clientSocket, address) = welcomeSocket.accept()
        print("[*] Accepted connection from: %s:%d" % (address[0], address[1]))
        clientSocket.send("HTTP/1.1 200 OK\r\n\r\n".encode())
        clientSocket.close()
    except KeyboardInterrupt:
        print("[*] Shutting down the server...")
        welcomeSocket.close()
        sys.exit(0)
    except Exception as e:
        print("[*] Exception: %s" % (e))
        continue
