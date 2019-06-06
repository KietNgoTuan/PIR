import socket
import sys
import os
import threading
import hashlib
import shutil
import copy
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
    dif = os.stat(f2).st_size-os.stat(f1).st_size
    tab = bytearray(abs(dif))
    for i in range(abs(dif)):
        tab[i]=0

    file2 = open(f1 , 'ab+')
    file2.write(tab)
    file2.close()


def depadding(f,size):
    fi=open(f,"rb+")
    tab=fi.read()
    temp=tab[:size]
    fi.seek(0)
    fi.truncate()
    fi.write(temp)
    fi.close()


def get_largest_file(all_files):
    """
    Take all path and return its size and its position in the list
    :param all_files: all concerned files
    :return: PATH, SIZE (tuple)
    """
    max = int()
    path = str()
    for i in all_files:
        if os.stat(i).st_size > max:
                max = os.stat(i).st_size
                path = i
    return path, max

def encode(all_files, f3):
    """
    :param all_files: all files that must be XOR together
    :param f3: outfile
    :return: outfile
    """
    path , max_size = get_largest_file(all_files)
    print(path)
    print(max_size)
    temp_list = copy.deepcopy(all_files)
    print(temp_list)
    temp_list.remove(path)
    print(temp_list)
    temp_file_list = list()

    for each_path in range(len(temp_list)):
        temp_file = os.getcwd()+"/temp_file/"+temp_list[each_path].split("/")[-1].split(".")[0]+"_temp.mp4"
        temp_file_list.append(temp_file)
        shutil.copyfile(temp_list[each_path], temp_file_list[each_path],  follow_symlinks=True)
        padding(temp_file_list[each_path], path)

    temp_file_list.append(path)
    result = bytearray(max_size)
    list_file = list()
    for each_path in temp_file_list:
        f = open(each_path, 'rb')
        list_file.append(f)
    with open(f3, 'wb') as file_out:
        byte_list = list()
        for each_elt in range(len(all_files)):
            byte_list.append(bytearray(list_file[each_elt].read()))

        for byte1 in range(max_size):
            result[byte1] = 0
            for file in byte_list:
                result[byte1] ^= file[byte1]
        file_out.write(result)

    for f in list_file:
        f.close()
    temp_file_list.pop()
    for file in temp_file_list:
        os.remove(file)



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
                ONGOING_REQUESTS.add((hash, os.stat(INDEX_VIDEOS[hash]).st_size))
                print(ONGOING_REQUESTS)
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
                for (i,_) in ONGOING_REQUESTS:
                    ongoing_files.append(INDEX_VIDEOS[i])

                print(ongoing_files)

                parent_path = os.getcwd().split("\\")
                parent_path.pop()
                ongoing_files.append("C:/Users/matth/PycharmProjects/PIR/videos/BONGO.mp4")
                encode(ongoing_files,  "\\".join(parent_path)+"\\videos/sending.mp4")
                mutex_handle_client.acquire()
                broadcast_answer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                broadcast_answer.bind(('', BROADCAST_PORT))
                broadcast_answer.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                message = "[FILES]:"
                message += str(ongoing_files)


                print(message)
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





