import socket
import sys
import os
import threading
import hashlib
import time


NB_CLIENT = 10
PORT = 25555
BROADCAST_PORT = 44444

INDEX_VIDEOS = dict()
CLIENTS_CACHE = dict()


mutex_clients_cache = threading.Lock()
"""
Creation de l'indexage des vidéos 
"""

for title in os.listdir("../videos"):
    hash = hashlib.md5()
    hash.update(bytes(title.split(".")[0], "utf-8"))
    path = os.getcwd().split("\\")
    path.pop()
    real_path = '\\'.join(path)+"/videos/"+title
    INDEX_VIDEOS[hash.hexdigest()] = real_path


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', PORT))



n = 0
tabClients = dict()
print(INDEX_VIDEOS)

def padding(f1,f2):
    size=0
    dif = os.stat(f1).st_size-os.stat(f2).st_size
    print(dif)
    tab = bytearray(abs(dif))
    for i in range(abs(dif)):
        tab[i]=0
    if dif == 0:
        size=0
    if dif >0:
        size=os.stat(f2).st_size
        file2 = open(f2, 'ab+')
        file2.write(tab)
        file2.close()
    elif dif<0:
        size=os.stat(f1).st_size
        file1 = open(f1, 'ab+')
        file1.write(tab)
        file1.close()
    return size

def depadding(f,size):
    fi=open(f,"rb+")
    tab=fi.read()
    temp=tab[:size]
    fi.seek(0)
    fi.truncate()
    fi.write(temp)
    fi.close()
def couper(f,size):
        fi=open(f,"rb+")
        tab=fi.read()

        temp=tab[size:]
        fi.seek(0)
        fi.truncate()
        fi.write(temp)
        fi.close()

def encode(f1,f2,f3):
        smallsize=padding(f1,f2)
        s="%032d" % int(bin(smallsize)[2:])
        tabsize=bytearray(s.encode())
        size=os.stat(f1).st_size
        result=bytearray(size)
        with open(f1, 'rb') as file1:
            with open(f2, 'rb') as file2:
                with open(f3, 'wb') as file_out:
                    fi1=bytearray(file1.read())
                    fi2=bytearray(file2.read())
                    for byte1 in range(size):
                        result[byte1]=(fi1[byte1]^fi2[byte1])
                    if smallsize == 0:
                      tab=result
                    else:
                      tab=tabsize+result
                    file_out.write(tab)
                    print(os.stat(f3).st_size)
                    return f3




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
            hash = response.decode("utf-8").split("+")[0]
            cache_information = response.decode("utf-8").split("+")[1]

            mutex_clients_cache.acquire()
            if ip not in CLIENTS_CACHE.keys():
                CLIENTS_CACHE[ip] = cache_information
            elif CLIENTS_CACHE[ip] != cache_information:
                CLIENTS_CACHE[ip] = cache_information
            mutex_clients_cache.release()


            print(CLIENTS_CACHE)

            broadcast_answer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            broadcast_answer.bind(('',BROADCAST_PORT))
            broadcast_answer.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            print(INDEX_VIDEOS[hash])
            full_size = int()
            with open(INDEX_VIDEOS[hash], 'rb') as file_in:
                f = file_in.read(4096)
                while (f):
                    full_size += len(f)
                    try:
                        broadcast_answer.sendto(f ,("<broadcast>", 40000))
                    except:
                        print("eeeeeeeeeeeeeeeeerrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
                    f = file_in.read(4096)

            print(full_size)
            file_in.close()
            broadcast_answer.close()


        # print("Client déconnecté...")


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




