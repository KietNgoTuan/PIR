import socket
import sys
import os
import json
import threading
import hashlib
import matrix.matrix as m
import requests
import mysql.connector # Must be manually installed (pip install mysql-connector)
import time
import multiprocessing
import copy


def get_ideal_d2d(list_ip):
    """
    takes a list of ip and find the one with the largenst amount of opened ports
    :return: THE ip
    """
    max_val = 0
    ideal_ip = str()
    print("Host port : {}".format(D2D_HOST_PORT))
    for each_ip in list_ip:
        if len(D2D_HOST_PORT[each_ip]) >= max_val:
            ideal_ip = each_ip
    print(ideal_ip)
    return ideal_ip



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


def encode_data(size, result, ns, q):
    i = 0
    for byte in range(size):
        for file in ns:
            try:
                result[byte] ^= file[i]
            except IndexError:
                ns.remove(file)
        i +=1
    q.put(result)


def get_all_frag_threading(size):
    ref = PROCESS_ENCODE+1
    size_list = list()
    value = 0
    for i in range(ref):
        if i == ref-1:
            size_list.append(size)
            return size_list
        size_list.append(value)
        value += int(size / ref)



def encode(all_files, f3):
    """
    :param all_files: all files that must be XOR together
    :param f3: outfile
    :return: outfile
    """
    t_debut = time.time()
    path , max_size = get_largest_file(all_files)
    list_file = list()
    for each_path in all_files:
        f = open(each_path, 'rb')
        list_file.append(f)
    process_list = list()
    bytelist = list()
    result = bytearray(max_size)
    manager = multiprocessing.Manager()
    ns = manager.Namespace()
    with open(f3, 'wb') as file_out:
        for each_elt in range(len(all_files)):
            bytelist.append(bytearray(list_file[each_elt].read()))
        frag = get_all_frag_threading(max_size)
        print(frag)
        ns.result = [bytearray(frag[i+1]-frag[i]) for i in range(0, len(frag)-1)]
        q_list = [multiprocessing.Queue() for _ in range(0, len(frag)-1)]
        i = int()
        while i < len(frag)-1:
            temp_list = list()
            for elt in bytelist:
                if len(elt) > frag[i]:
                # _ = elt[frag[i+1]-1]
                    temp_list.append(elt[frag[i]:frag[i+1]])

            ns.bytelist = temp_list
            p = multiprocessing.Process(
                target = encode_data,
                args = (frag[i+1]-frag[i],ns.result[i] ,ns.bytelist, q_list[i])
            )
            process_list.append(p)
            p.start()
            i += 1

        for i in range(len(frag)-1):
            if i==len(frag)-1:
                result[frag[i]:max_size-1] = q_list[i].get()
            else:
                result[frag[i]:frag[i + 1]] = q_list[i].get()

        print(len(result))
        for p in process_list:
            p.join()

        file_out.write(result)
    for f in list_file:
        f.close()
    print("Temps final : {}".format(time.time()-t_debut))



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
        global SYNCHRONE_REQUEST, REQUIRED_FILES, D2D_HOST_PORT

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

                # Reinitialiser les ports de D2D
                for each_ip in CLIENTS_CACHE.keys():
                    D2D_HOST_PORT[each_ip] = D2D_PORT_DEST

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
                            print("Possible to D2D")
                            if len(REQUIRED_FILES[FILE_ID[each_coding[0]]]) == 1:
                                # Create D2D communication (possibly)
                                ip_src = REQUIRED_FILES[FILE_ID[each_coding[0]]][0]
                                ip_dest = list()
                                port_dest = int()
                                for cached_file in CLIENTS_CACHE.values():
                                    print(cached_file)
                                    print(FILE_ID[each_coding[0]])
                                    if FILE_ID[each_coding[0]] in cached_file:
                                        print(FILE_ID[each_coding[0]])
                                        ip_dest = [ipdest for (ipdest,hash) in CLIENTS_CACHE.items()
                                                   if FILE_ID[each_coding[0]] in hash ]

                                        if len(ip_dest) != 0:
                                            print("ip dest to get ideal from : {}".format(ip_dest))
                                            ip_dest = get_ideal_d2d(ip_dest)
                                            if len(D2D_HOST_PORT[ip_dest]) != 0:
                                                port_dest = D2D_HOST_PORT[ip_dest][0]
                                                print("ip_dest and port_dest : {},{}".format(ip_dest, port_dest))
                                                a = copy.deepcopy(D2D_HOST_PORT[ip_dest])
                                                a.pop(0)
                                                D2D_HOST_PORT[ip_dest] = a
                                                print(D2D_HOST_PORT)

                                if type(ip_dest) != list:
                                    cursor.execute("SELECT POPULARITY from pir.videos WHERE HASH_ID ='{}'"
                                                   .format(FILE_ID[each_coding[0]]))
                                    pop, = cursor.fetchall()
                                    pop, = pop
                                    message_bdcast = "[FILES_D2D]${}->{}".format(ip_src, ip_dest)
                                    print(message_bdcast)
                                    global REQUEST_ORIGIN
                                    broadcast_answer.sendto(bytes(message_bdcast, "utf-8"), ("<broadcast>", 40000))
                                    dest_data = {'port_dest':port_dest}
                                    message_dest = "[D2D_RECEIVER]$"+str(dest_data)
                                    print(message_dest)
                                    print("Request origin dict : {}".format(REQUEST_ORIGIN))
                                    try:
                                        print("Dest : {}".format(ip_dest))
                                        REQUEST_ORIGIN[ip_dest].send(bytes(message_dest, "utf-8"))
                                        dest_data = {'ip_dest': ip_dest,
                                                    'port_dest':port_dest,
                                                    'port_src':D2D_PORT_SRC,
                                                    'pop':pop}

                                        message_src = "[D2D_SENDER]$"+str(dest_data)
                                        REQUEST_ORIGIN[ip_src].send(bytes(message_src, "utf-8"))
                                        continue
                                    except socket.timeout:
                                        print("Didn't receive any answer")
                                        pass
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
                SYNCHRONE_REQUEST = 4

                del INDEX_REQUEST[:]
                del MATRIX_CODAGE[:]
                del index_files[:]
                del index_rest[:]
                del D2D_HOST[:]  # Theorical
                D2D_HOST_PORT = dict()
                print(REQUIRED_FILES)
                REQUIRED_FILES = dict()
                print("Temps pris en seconde pour répondre à tout le monde : {}".format(deltat))
                deltat = float()
                print("Temps pris en seconde pour répondre à tout le monde : {}".format(deltat))
                deltat = float()
            print("About to assign response")
            response = self.clientsocket.recv(4096)



if __name__ == "__main__":
    NB_CLIENT = 10
    PORT = 25555
    BROADCAST_PORT = 44444
    COEFF_LAN = 1.05

    D2D_PORT_SRC = 45000
    D2D_PORT_DEST = [45454, 45460, 45464]  # Un client peut gérer jusqu'à 3 D2D (MAX)
    PROCESS_ENCODE = multiprocessing.cpu_count()

    INDEX_VIDEOS = dict()
    INDEX_REQUEST = list()
    CLIENTS_CACHE = dict()
    REQUIRED_FILES = dict()  # for each file (hash) knows who asked for it
    MATRIX_CODAGE = list()
    deltat = float()
    ONGOING_REQUESTS = set()
    REQUEST_ORIGIN = dict()
    path_to_send = str()
    D2D_HOST = list()
    D2D_HOST_PORT = dict()

    PRIVATE_YOUTUBE_KEY = "AIzaSyDaKk0TDBSmnHSqmPXpmRCV2PApz8rJzqo"
    QUITTING = "7694f4a66316e53c8cdd9d9954bd611d"

    YOUTUBE_DICT = {
        "GRAVE": "_yyjPxvNLGk",
        "ALLAN": "_dK2tDK9grQ",
        "YEUX": "FmUDe7P0fzg",
        "ADIEU": "U4EICXeGtx0",
        "CACHE": "hNK5izw6jUs",
        "VERRA": "YltjliK0ZeA",
        "SICKO": "6ONRf7h3Mdk",
        "PSYCHO": "au2n7VVGv_c",
        "BETTER": "UYwF-jdcVjY",
        "TOUR": "WrsFXgQk5UI"
    }

    SYNCHRONE_REQUEST = 4
    AMOUNT_CLIENT = int()

    # Initializing connection with mySQL
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=str()
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
        real_path = '\\'.join(path) + "/videos/" + title
        if title.split(".")[0] not in all_names:
            popularity = requests.get("https://www.googleapis.com/youtube/v3/videos?part=statistics&id="
                                      + str(YOUTUBE_DICT[title.split(".")[0]]) + "&key=" + PRIVATE_YOUTUBE_KEY).content
            json_popularity = json.loads(popularity)
            parameters = (title.split(".")[0], hash.hexdigest(),
                          (0.5 * eval(json_popularity['items'][0]['statistics']['viewCount']) +
                           eval(json_popularity['items'][0]['statistics']["likeCount"])) /
                          (1.5 * eval(json_popularity['items'][0]['statistics']['dislikeCount']))
                          , real_path)
            request = "INSERT INTO PIR.VIDEOS (NOM,HASH_ID,POPULARITY,PATH) VALUES (%s,%s,%s,%s);"
            cursor.execute(request, parameters)
            connection.commit()

        INDEX_VIDEOS[hash.hexdigest()] = real_path

    FILE_ID = list(INDEX_VIDEOS.keys())

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))

    n = 0
    tabClients = dict()
    print(INDEX_VIDEOS)

    while True:
        try:
            s.listen(NB_CLIENT)
            print("En écoute...")
            (clientsocket, (ip, port)) = s.accept()  # on repere une connexion
            REQUEST_ORIGIN[ip]=clientsocket
            clientsocket.setblocking(True)


            tabClients[n] = clientsocket  # on rentre dans le dictionnaire des clients
            print("Client in it")
            newClientThread = ClientThread(ip, port, clientsocket, mutex_handle_client)  # on lance un thread pour gérer le client
            newClientThread.start()

            AMOUNT_CLIENT += 1


        except KeyboardInterrupt:
            for i in range(n):
                tabClients[i].close()
            sys.exit(0)





