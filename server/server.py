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


NB_CLIENT = 10
PORT = 25555
BROADCAST_PORT = 44444
COEFF_LAN = 1.15

INDEX_VIDEOS = dict()

CLIENTS_CACHE = dict()
INDEX_REQUEST=list()
MATRIX_CODAGE=list()

ONGOING_REQUESTS = set()

PRIVATE_YOUTUBE_KEY = "AIzaSyDaKk0TDBSmnHSqmPXpmRCV2PApz8rJzqo"
QUITTING = "7694f4a66316e53c8cdd9d9954bd611d"

YOUTUBE_DICT = {
    "BONGO" : "bHnuWN7z8gk",
    "ALLAN" :  "_dK2tDK9grQ",
    "TOUR" : "VcyFfcJbyeM",
    "KALI" : "7ysFgElQtjI",
    "NYAN" : "uKm2KN5gBiY"
}

SYNCHRONE_REQUEST = 5
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
        parameters = (title.split(".")[0],hash.hexdigest(), eval(json_popularity['items'][0]['statistics']['viewCount'])
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
    for file in temp_file_list:
        os.remove(file)

def MatrixCodage(matrix,file):
    fichi=m.MatrixDifRequeste(matrix,file)
    result=list()
    if(m.RequestIsRelatif(fichi)==True):
      xor=m.TraitementXOR(fichi)
      mes=m.XORfinal(xor)
      result=m.ChoixMsg(mes,file)
    print("Result : {}".format(result))
    for i in file:

     result.append([i])
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
        global SYNCHRONE_REQUEST

        if response.decode("utf-8").split("+")[0] != QUITTING and SYNCHRONE_REQUEST > 0:
            print("Start while : {}".format(response.decode("utf-8")))
            hash = response.decode("utf-8").split("+")[0]
            index = FILE_ID.index(hash)  # Prendre l' indice du fichier demande
            vector_cache = [0 for _ in range(len(FILE_ID))]
            with mutex_ongoing_request:
                ONGOING_REQUESTS.add((hash, os.stat(INDEX_VIDEOS[hash]).st_size))
                get_popularity_request = "SELECT POPULARITY FROM pir.videos WHERE HASH_ID='{}';".format(hash)
                cursor.execute(get_popularity_request)
                popularity, = cursor.fetchall()[0]
                request = "UPDATE pir.videos SET POPULARITY='{}' WHERE HASH_ID='{}'".format(popularity*COEFF_LAN, hash)
                cursor.execute(request)
                connection.commit()
            cache_information = response.decode("utf-8").split("+")[1]
            cache_information=eval(cache_information)


            mutex_clients_cache.acquire()
            if ip not in CLIENTS_CACHE.keys():
                CLIENTS_CACHE[ip] = cache_information
            elif CLIENTS_CACHE[ip] != cache_information:
                CLIENTS_CACHE[ip] = cache_information
            mutex_clients_cache.release()

            for cache in cache_information:
                vector_cache[FILE_ID.index(cache)] = 1
            INDEX_REQUEST.append((index, vector_cache))
            with mutex_handle_client:
                SYNCHRONE_REQUEST -= 1
            print("Requetes restantes : {}".format(SYNCHRONE_REQUEST))


            if SYNCHRONE_REQUEST == 0:
                broadcast_answer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                broadcast_answer.bind(('', BROADCAST_PORT))
                broadcast_answer.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                INDEX_REQUEST.sort(key=lambda x: x[0])
                index_files = list()
                for index in INDEX_REQUEST:
                    MATRIX_CODAGE.append(index[1])
                    index_files.append(index[0])
                # res to be send (optimal one)
                res = MatrixCodage(MATRIX_CODAGE, index_files)
                message = "[SENDINGS]$"+str(len(res))
                broadcast_answer.sendto(bytes(message, "utf-8"), ("<broadcast>", 40000))

                print(MATRIX_CODAGE)

                ongoing_files_size = list()
                ongoing_files = list()
                parent_path = os.getcwd().split("\\")
                parent_path.pop()

                print("ONGOING REQUEST : {}".format(ONGOING_REQUESTS))
                for (i,size) in ONGOING_REQUESTS:
                    ongoing_files.append(INDEX_VIDEOS[i])
                    ongoing_files_size.append((i,size))
                    print("FILES ABOUT TO BE SEND : {}".format(ongoing_files_size))

                if len(ongoing_files) == 1:
                    path_to_send = [a for a in ongoing_files][0]
                    message = "[FILES]$"
                    message += str([a for a in ONGOING_REQUESTS])
                    print("Messgae in ongoing_files == 1")
                    with open(path_to_send, 'rb') as file_in:
                        f = file_in.read(1024)
                        while (f):
                            broadcast_answer.sendto(f, ("<broadcast>", 40000))
                            f = file_in.read(1024)
                    file_in.close()

                else:

                    for each_coding in res:
                        print("Each coding : {}".format(res[0]))
                        # List index : each_coding
                        if len(each_coding) == 1:
                            path_to_send = INDEX_VIDEOS[FILE_ID[each_coding[0]]]


                        else :
                            path_to_send = "\\".join(parent_path) + "\\videos/sending.mp4"
                            to_encode = [INDEX_VIDEOS[FILE_ID[index]] for index in each_coding]
                            print("Files to encode : {}".format(to_encode))
                            encode(to_encode, path_to_send)
                            print("Size of sending : {}".format(os.stat(path_to_send).st_size))

                        message = "[FILES]$"

                        message += str([(FILE_ID[index],
                                         os.stat(INDEX_VIDEOS[FILE_ID[index]]).st_size) for index in each_coding])
                        print("Message regarding files : {}".format(message))
                        broadcast_answer.sendto(bytes(message, "utf-8"),  ("<broadcast>", 40000))

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

                    broadcast_answer.close()
                    SYNCHRONE_REQUEST = 5

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





