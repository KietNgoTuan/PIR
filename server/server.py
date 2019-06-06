import socket
import sys
import os
import threading
import hashlib
import shutil
import time


NB_CLIENT = 10
PORT = 25555
BROADCAST_PORT = 44444

INDEX_VIDEOS = dict()
CLIENTS_CACHE = dict()


ONGOING_REQUESTS = set()
QUITTING = "7694f4a66316e53c8cdd9d9954bd611d"

SYNCHRONE_REQUEST = 2
AMOUNT_CLIENT = int()



mutex_clients_cache = threading.Lock()
mutex_ongoing_request = threading.Lock()
mutex_handle_client = threading.Lock()

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

    #
# def depadding(f,size):
#     fi=open(f,"rb+")
#     tab=fi.read()
#     temp=tab[:size]
#     fi.seek(0)
#     fi.truncate()
#     fi.write(temp)
#     fi.close()

def couper(f,size):
        fi=open(f,"rb+")
        tab=fi.read()

        temp=tab[size:]
        fi.seek(0)
        fi.truncate()
        fi.write(temp)
        fi.close()


def encode(f1, f2, f3):
    if os.stat(f1).st_size < os.stat(f2).st_size:
        shutil.copyfile(f1, "temp_file.mp4", follow_symlinks=True)
        smallsize = padding("temp_file.mp4", f2)
    else:
        shutil.copyfile(f2, "temp_file.mp4", follow_symlinks=True)
        smallsize = padding(f1, "temp_file.mp4")

    print("Smallsize : {}".format(smallsize))
    s = "%032d" % int(bin(smallsize)[2:])
    tabsize = bytearray(s.encode())
    size_f1 = os.stat(f1).st_size
    size_f2 = os.stat(f2).st_size
    result = bytearray(max(size_f1, size_f2))
    if os.stat(f1).st_size < os.stat(f2).st_size:
        with open("temp_file.mp4", 'rb') as file1:
            with open(f2, 'rb') as file2:
                with open(f3, 'wb') as file_out:
                    fi1 = bytearray(file1.read())
                    fi2 = bytearray(file2.read())

                    for byte1 in range(max(size_f1, size_f2)):
                        result[byte1] = (fi1[byte1] ^ fi2[byte1])
                    tab = tabsize + result
                    file_out.write(tab)

        os.remove(os.getcwd() + "/temp_file.mp4")
        return f3

    else:
        with open(f1, 'rb') as file1:
            with open("temp_file.mp4", 'rb') as file2:
                with open(f3, 'wb') as file_out:
                    fi1 = bytearray(file1.read())
                    fi2 = bytearray(file2.read())
                    for byte1 in range(max(size_f1, size_f2)):
                        result[byte1] = (fi1[byte1] ^ fi2[byte1])
                    tab = tabsize + result
                    file_out.write(tab)
        os.remove(os.getcwd() + "/temp_file.mp4")
        return f3


class ClientThread(threading.Thread):
    FILE_FOUND = False

    def __init__(self, ip, port, clientsocket, semaphoreClient):

        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.clientsocket = clientsocket
        self.semaphoreClient = semaphoreClient
        print("[+] Nouveau thread pour %s %s" % (self.ip, self.port,))

    def run(self):  # cette fonction va gérer ce qu'on envoit et reçoit du client

        print("Connexion de %s %s" % (self.ip, self.port,))
        response = self.clientsocket.recv(4096)  # reçoit le message sur un buffer de 4096 bits
        global SYNCHRONE_REQUEST

        if response.decode("utf-8").split("+")[0] != QUITTING and SYNCHRONE_REQUEST > 0:
            print("Start while : {}".format(response.decode("utf-8")))
            hash = response.decode("utf-8").split("+")[0]
            with mutex_ongoing_request:
                global ONGOING_REQUESTS
                ONGOING_REQUESTS.add(hash)
            print(ONGOING_REQUESTS)
            cache_information = response.decode("utf-8").split("+")[1]

            mutex_clients_cache.acquire()
            if ip not in CLIENTS_CACHE.keys():
                CLIENTS_CACHE[ip] = cache_information
            elif CLIENTS_CACHE[ip] != cache_information:
                CLIENTS_CACHE[ip] = cache_information
            mutex_clients_cache.release()

            with mutex_handle_client:
                SYNCHRONE_REQUEST -= 1
            print("Requetes restantes : {}".format(SYNCHRONE_REQUEST))


            if SYNCHRONE_REQUEST == 0:

                ongoing_files = list()
                for i in ONGOING_REQUESTS:
                    ongoing_files.append(i)

                parent_path = os.getcwd().split("\\")
                parent_path.pop()
                encode(INDEX_VIDEOS[ongoing_files[0]], INDEX_VIDEOS[ongoing_files[1]],  "\\".join(parent_path)+"\\videos/sending.mp4")
                mutex_handle_client.acquire()
                broadcast_answer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                broadcast_answer.bind(('', BROADCAST_PORT))
                broadcast_answer.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                message = "[FILES]:"
                for elt in ONGOING_REQUESTS:
                    message += elt+"+"

                broadcast_answer.sendto(bytes(message, "utf-8"),  ("<broadcast>", 40000))

                with open('../videos/sending.mp4', 'rb') as file_in:
                    f = file_in.read(1024)
                    while (f):
                        broadcast_answer.sendto(f, ("<broadcast>", 40000))
                        f = file_in.read(1024)
                file_in.close()
                os.remove( "\\".join(parent_path)+"\\videos/sending.mp4")
                broadcast_answer.close()
                SYNCHRONE_REQUEST = 2
                mutex_handle_client.release()
            
        print('Client disconnected')



while True:
    try:
        s.listen(NB_CLIENT)
        print("En écoute...")

        (clientsocket, (ip, port)) = s.accept()  # on repere une connexion
        clientsocket.setblocking(True)

        tabClients[n] = clientsocket  # on rentre dans le dictionnaire des clients

        newClientThread = ClientThread(ip, port, clientsocket, mutex_handle_client)  # on lance un thread pour gérer le client
        newClientThread.start()

        AMOUNT_CLIENT += 1


    except KeyboardInterrupt:
        for i in range(n):
            tabClients[i].close()
        print('Je ferme les connexions')
        sys.exit(0)





