import socket
import sys
import os
import threading
from functools import partial

NB_CLIENT = 10
PORT = 25555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', PORT))

n = 0
tabClients = dict()


class ClientThread(threading.Thread):
    FILE_FOUND = False

    def __init__(self, ip, port, clientsocket):

        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.clientsocket = clientsocket
        print("[+] Nouveau thread pour %s %s" % (self.ip, self.port,))

    def run(self):  # cette fonction va gérer ce qu'on envoit et reçoit du client

        print("Connexion de %s %s" % (self.ip, self.port,))

        response = self.clientsocket.recv(4096)  # reçoit le message sur un buffer de 4096 bits

        if response != str():
            response = response.decode("utf-8")
            print(response)
            files = os.listdir("../videos")
            for eachFile in files:
                if response in eachFile:
                    FILE_FOUND = True
                    binary_file = str()
                    print(eachFile.split(".")[0])
                    with open("../videos/" + eachFile, 'rb') as file_in:
                        f = file_in.read(4096)
                        while (f):
                            clientsocket.send(f)
                            f = file_in.read(4096)
                    file = "key:" + eachFile.split(".")[0]
                    clientsocket.send(bytes(file, "utf-8"))
                    file_in.close()
            if not FILE_FOUND:
                clientsocket.send(b"File not found")

        print("Client déconnecté...")


try:
    tabClients = {}
    n = 0

    while True:
        s.listen(NB_CLIENT)
        print("En écoute...")

        (clientsocket, (ip, port)) = s.accept()  # on repere une connexion

        tabClients[n] = clientsocket  # on rentre dans le dictionnaire des clients

        newClientThread = ClientThread(ip, port, clientsocket)  # on lance un thread pour gérer le client
        newClientThread.start()

        n += 1


except KeyboardInterrupt:
    print('Exiting...')

except:
    for i in range(n):
        tabClients[i].close()
print('Je ferme les connexions')
sys.exit()
pass




