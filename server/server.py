import socket
import sys
import os
import json
import threading
import hashlib
import shutil
import copy
import matrix.matrix as m
import requests
import mysql.connector # Must be manually installed (pip install mysql-connector)
import time

NB_CLIENT = 10
PORT = 25555
BROADCAST_PORT = 44444
COEFF_LAN = 1.05

D2D_PORT_SRC = 45000
D2D_PORT_DEST = 45454

INDEX_VIDEOS = dict()
INDEX_REQUEST = list()
CLIENTS_CACHE = dict()
REQUIRED_FILES = dict() # for each file (hash) knows who asked for it
MATRIX_CODAGE=list()
deltat = float()
ONGOING_REQUESTS = set()
REQUEST_ORIGIN = dict()
path_to_send = str()
D2D_HOST = list()

PRIVATE_YOUTUBE_KEY = "AIzaSyDaKk0TDBSmnHSqmPXpmRCV2PApz8rJzqo"
QUITTING = "7694f4a66316e53c8cdd9d9954bd611d"

YOUTUBE_DICT = {
    "BONGO" : "bHnuWN7z8gk",
    "ALLAN" : "_dK2tDK9grQ",
    "TOUR" :  "VcyFfcJbyeM",
    "KALI" :  "7ysFgElQtjI",
    "NYAN" :  "uKm2KN5gBiY"
}

SYNCHRONE_REQUEST = 2
AMOUNT_CLIENT = int()

# Initializing connection with mySQL
try:
    connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password = str()
)

    cursor = connection.cursor()
except mysql.connector.errors:
    print("Cannot reach database...")
    sys.exit(0)

mutex_clients_cache = threading.Lock()
mutex_ongoing_request = threading.Lock()
mutex_handle_client = threading.Lock()

"""
Creation de l'indexage des vidéos 
"""

cursor.execute("SELECT NOM FROM pir.videos;")
all_names = [name for (name,) in cursor.fetchall()]
for title in os.listdir("../videos"):
    hash = hashlib.md5()
    hash.update(bytes(title.split(".")[0], "utf-8"))
    path = os.getcwd().split("\\")
    path.pop()
    real_path = '\\'.join(path)+"/videos/"+title
    if title.split(".")[0] not in all_names:
        popularity = requests.get("https://www.googleapis.com/youtube/v3/videos?part=statistics&id="
                              +str(YOUTUBE_DICT[title.split(".")[0]])+"&key="+PRIVATE_YOUTUBE_KEY).content
        json_popularity = json.loads(popularity)
        parameters = (title.split(".")[0],hash.hexdigest(),
                      (0.5*eval(json_popularity['items'][0]['statistics']['viewCount'])+
                       eval(json_popularity['items'][0]['statistics']["likeCount"]))/
                      (1.5*eval(json_popularity['items'][0]['statistics']['dislikeCount']))
                      ,real_path)
        request = "INSERT INTO PIR.VIDEOS (NOM,HASH_ID,POPULARITY,PATH) VALUES (%s,%s,%s,%s);"
        cursor.execute(request, parameters)
        connection.commit()

    INDEX_VIDEOS[hash.hexdigest()] = real_path

FILE_ID=list(INDEX_VIDEOS.keys())

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
    print("Temp file lisr : {}".format(temp_file_list))
    for file in temp_file_list:
        os.remove(file)

def MatrixCodage(matrix,file):
    fichi=m.MatrixDifRequeste(matrix,file)
    result=list()
    if(m.RequestIsRelatif(fichi)==True):
      xor=m.TraitementXOR(fichi)
      mes=m.XORfinal(xor)
      result=m.ChoixMsg(mes,file)
    else:
        for i in file:
            result.append([i])
    print("Result"+str(result))
    return result


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
        global SYNCHRONE_REQUEST, REQUIRED_FILES

        while response.decode("utf-8").split("+")[0] != QUITTING:
            print("Start while : {}".format(response.decode("utf-8")))
            hash = response.decode("utf-8").split("+")[0]

            print("Hash : {}".format(hash))
            index = FILE_ID.index(hash)  # Prendre l' indice du fichier demande
            vector_cache = [0 for _ in range(len(FILE_ID))]
            with mutex_ongoing_request:
                try:
                    REQUIRED_FILES[hash].append(self.ip)
                except KeyError:
                    REQUIRED_FILES[hash] = [self.ip]
                ONGOING_REQUESTS.add((hash, os.stat(INDEX_VIDEOS[hash]).st_size))
                get_popularity_request = "SELECT POPULARITY FROM pir.videos WHERE HASH_ID='{}';".format(hash)
                cursor.execute(get_popularity_request)
                popularity, = cursor.fetchall()[0]
                request = "UPDATE pir.videos SET POPULARITY='{}' WHERE HASH_ID='{}'".format(popularity*COEFF_LAN, hash)
                cursor.execute(request)
                connection.commit()
            cache_information = response.decode("utf-8").split("+")[1]
            cache_information=eval(cache_information)

            print("Cache information : {}".format(cache_information))
            mutex_clients_cache.acquire()
            print("KEYS : {}".format(CLIENTS_CACHE.keys()))
            print("Client IP : {}".format(self.ip))
            if self.ip not in CLIENTS_CACHE.keys():
                CLIENTS_CACHE[self.ip] = cache_information
            elif CLIENTS_CACHE[self.ip] != cache_information:
                CLIENTS_CACHE[self.ip] = cache_information
            print(CLIENTS_CACHE)
            mutex_clients_cache.release()
            for cache in cache_information:
                vector_cache[FILE_ID.index(cache)]=1
            if INDEX_REQUEST == []:
                INDEX_REQUEST.append([index, 0, vector_cache])
            else:
                check = 0
                for indice in INDEX_REQUEST:
                    if indice[0] == index:
                        indice[1] = indice[1] + 1
                        check = 1
                if check == 0:
                    INDEX_REQUEST.append([index, 0, vector_cache])
            with mutex_handle_client:
                SYNCHRONE_REQUEST -= 1
            print("Requetes restantes : {}".format(SYNCHRONE_REQUEST))
            full_size = int()

            if SYNCHRONE_REQUEST == 0:
                print("About to send synchrone request")
                broadcast_answer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                broadcast_answer.bind(('', BROADCAST_PORT))
                broadcast_answer.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                print("Index Request : {}".format(INDEX_REQUEST))
                INDEX_REQUEST.sort(key=lambda x: x[0])
                index_files = list()
                index_rest = list()
                for index in INDEX_REQUEST:
                    print("Index : {}".format(index))
                    if index[1] == 0:
                        MATRIX_CODAGE.append(index[2])
                        print(index[0])
                        index_files.append(index[0])
                    else:
                        index_rest.append(index[0])
                # res to be send (optimal one)
                res = MatrixCodage(MATRIX_CODAGE, index_files)
                print(" ir "+str(index_rest))
                print("if"+str(index_files))
                if len(index_rest) != 0:
                    for i in index_rest:
                        res.append([i])

                print("RES : {}".format(res))
                message = "[SENDINGS]$"+str(len(res))
                print("Message : {}".format(message))
                broadcast_answer.sendto(bytes(message, "utf-8"), ("<broadcast>", 40000))

                print(MATRIX_CODAGE)

                ongoing_files_size = list()
                ongoing_files = list()
                parent_path = os.getcwd().split("\\")
                parent_path.pop()
                print("ONGOING REQUEST : {}".format(ONGOING_REQUESTS))
                for (i,size) in ONGOING_REQUESTS:
                    ongoing_files.append(INDEX_VIDEOS[i])
                    full_size += size
                    ongoing_files_size.append((i,size))
                    print("FILES ABOUT TO BE SEND : {}".format(ongoing_files_size))

                if len(ongoing_files) == 1:
                    path_to_send = [a for a in ongoing_files][0]
                    message = "[FILES]$"
                    to_send = list()
                    for (a,b) in ONGOING_REQUESTS:
                        cursor.execute("SELECT POPULARITY FROM pir.videos WHERE HASH_ID='{}'".format(a))
                        pop, = cursor.fetchall()[0]
                        to_send.append((a,b,pop))
                    message += str(to_send)
                    tdebut = time.time()
                    broadcast_answer.sendto(bytes(message, "utf-8"), ("<broadcast>", 40000))
                    with open(path_to_send, 'rb') as file_in:
                        f = file_in.read(1024)
                        while (f):
                            broadcast_answer.sendto(f, ("<broadcast>", 40000))
                            f = file_in.read(1024)
                    inter_t = (time.time() - tdebut)
                    global deltat
                    deltat += inter_t
                    file_in.close()

                else:
                    for each_coding in res:
                        # List index : each_coding
                        if len(each_coding) == 1:
                            leave = False
                            print("Possible to D2D")
                            if len(REQUIRED_FILES[FILE_ID[each_coding[0]]]) == 1:
                                # Create D2D communication (possibly)
                                ip_src = REQUIRED_FILES[FILE_ID[each_coding[0]]][0]
                                ip_dest = list()
                                print(CLIENTS_CACHE)
                                print(CLIENTS_CACHE.items())
                                for cached_file in CLIENTS_CACHE.values():
                                    print(cached_file)
                                    print(FILE_ID[each_coding[0]])
                                    if FILE_ID[each_coding[0]] in cached_file:
                                        print(FILE_ID[each_coding[0]])
                                        ip_dest = [ipdest for (ipdest,hash) in CLIENTS_CACHE.items()
                                                   if FILE_ID[each_coding[0]] in hash ]

                                        print("Voici ip_dest : {}".format(ip_dest))
                                        if len(ip_dest) != 0:
                                            for i in ip_dest:
                                                if i not in D2D_HOST:
                                                    ip_dest = i
                                                    D2D_HOST.append(ip_dest)
                                                    break
                                if ip_dest != list():
                                    cursor.execute("SELECT POPULARITY from pir.videos WHERE HASH_ID ='{}'"
                                                   .format(FILE_ID[each_coding[0]]))
                                    pop, = cursor.fetchall()
                                    pop, = pop
                                    print(pop)
                                    message_bdcast = "[FILES_D2D]${}->{}".format(ip_src, ip_dest)
                                    print(message_bdcast)
                                    global REQUEST_ORIGIN
                                    broadcast_answer.sendto(bytes(message_bdcast, "utf-8"), ("<broadcast>", 40000))
                                    dest_data = {'port_dest':D2D_PORT_DEST }
                                    message_dest = "[D2D_RECEIVER]$"+str(dest_data)
                                    print(message_dest)

                                    REQUEST_ORIGIN[ip_dest].send(bytes(message_dest, "utf-8"))
                                    dest_data = {'ip_dest': ip_dest,
                                                    'port_dest':D2D_PORT_DEST,
                                                    'port_src':D2D_PORT_SRC,
                                                    'pop':pop}

                                    message_src = "[D2D_SENDER]$"+str(dest_data)
                                    REQUEST_ORIGIN[ip_dest].settimeout(3)
                                    try:
                                        data = REQUEST_ORIGIN[ip_dest].recv(4096)
                                        print("DATA from dest : {}".format(data))
                                        if "[READY_D2D]" not in data.decode("utf-8"):
                                            raise socket.timeout
                                        else:
                                            continue
                                    except socket.timeout:
                                        leave = True
                                    if not leave:
                                        REQUEST_ORIGIN[ip_src].send(bytes(message_src, "utf-8"))
                                      # Goes to the next iteration
                                """
                                    [D2D_SENDER] : Initialize connection and will ask for the file
                                    [D2D_RECEIVER] : Receive the request and send through TCP to D2D_SENDER
                                                                    
                                """

                            path_to_send = INDEX_VIDEOS[FILE_ID[each_coding[0]]]

                        else :
                            path_to_send = "\\".join(parent_path) + "\\videos/sending.mp4"
                            to_encode = [INDEX_VIDEOS[FILE_ID[index]] for index in each_coding]
                            print("Files to encode : {}".format(to_encode))
                            encode(to_encode, path_to_send)
                            print("Size of sending : {}".format(os.stat(path_to_send).st_size))
                        message = "[FILES]$"
                        value = list()
                        for index in each_coding:
                            cursor.execute("SELECT POPULARITY FROM pir.videos WHERE HASH_ID='{}';".format(FILE_ID[index]))
                            pop,= cursor.fetchall()[0]
                            value.append((FILE_ID[index],
                                         os.stat(INDEX_VIDEOS[FILE_ID[index]]).st_size, pop))
                        message += str(value)
                        print("Message regarding files : {}".format(message))
                        broadcast_answer.sendto(bytes(message, "utf-8"),  ("<broadcast>", 40000))
                        tdebut = time.time()

                        with open(path_to_send, 'rb') as file_in:
                            f = file_in.read(1024)
                            while (f):
                                broadcast_answer.sendto(f, ("<broadcast>", 40000))
                                f = file_in.read(1024)
                        file_in.close()
                        try:
                            os.remove( "\\".join(parent_path)+"\\videos/sending.mp4")
                        except FileNotFoundError:
                            pass
                        inter_t = (time.time()-tdebut)
                        deltat += inter_t

                    broadcast_answer.close()
                del INDEX_REQUEST[:]
                del MATRIX_CODAGE[:]
                del index_files[:]
                del index_rest[:]
                del D2D_HOST[:] # Theorical
                print(REQUIRED_FILES)
                REQUIRED_FILES = dict()
                print("REUPDATE")
                SYNCHRONE_REQUEST = 2
                print(SYNCHRONE_REQUEST)
                print("Temps pris en seconde pour répondre à tout le monde : {}".format(deltat))
            response = self.clientsocket.recv(4096)



while True:
    try:
        s.listen(NB_CLIENT)
        print("En écoute...")
        (clientsocket, (ip, port)) = s.accept()  # on repere une connexion
        REQUEST_ORIGIN[ip]=clientsocket
        clientsocket.setblocking(True)


        tabClients[n] = clientsocket  # on rentre dans le dictionnaire des clients

        newClientThread = ClientThread(ip, port, clientsocket, mutex_handle_client)  # on lance un thread pour gérer le client
        newClientThread.start()

        AMOUNT_CLIENT += 1


    except KeyboardInterrupt:
        for i in range(n):
            tabClients[i].close()
        sys.exit(0)





