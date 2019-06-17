import socket
import os
import hashlib
import tempfile
import time
import sys
import copy
import threading
import multiprocessing


"""
Code to check all files stored in temp memory
"""

def insert(tuple):
    hash,pop = tuple
    global QUEUE_CACHE
    for (queue_hash, queue_pop) in QUEUE_CACHE:
        if pop < queue_pop:
                return QUEUE_CACHE.insert(QUEUE_CACHE.index((queue_hash, queue_pop)), (hash,pop))
    return QUEUE_CACHE.append((hash,pop))




"""
    Utilisation du module D2D
"""


class D2DTCPThreading(threading.Thread):

    def __init__(self, tcp_connection, hash_id, time):
        threading.Thread.__init__(self)
        self.tcp_connection = tcp_connection
        self.hash_id = hash_id
        self.time_debut = time


    def run(self):
        data = self.tcp_connection.recv(4096)
        data_utf8 = data.decode("utf-8")
        print(data_utf8)
        if "[D2D_SENDER]" in data_utf8:
            amount_of_try = 5
            payload = eval(data_utf8.split("$")[1])
            d2d_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.SO_REUSEADDR)
            d2d_tcp.bind(('', payload["port_src"]))

            while (amount_of_try >= 0):
                try:
                    d2d_tcp.connect((payload["ip_dest"], payload["port_dest"]))
                    break
                except socket.error:
                    print("Error trying again to initialize connection")
                    time.sleep(1)
                    if amount_of_try == 0:
                        print("Can no longer succed")
                        sys.exit(0)
                    amount_of_try -= 1

            message = "[FILE_REQUEST]${}".format(self.hash_id)
            print(message)
            d2d_tcp.send(bytes(message, "utf-8"))

            with open(tempfile.gettempdir() + "/" + self.hash_id + ".mp4", "wb") as mp4file:
                while (True):
                    data = d2d_tcp.recv(1024)
                    mp4file.write(data)
                    try:
                        if "[END]" in  data.decode("utf-8") or data.decode("utf-8") == str():
                            break
                    except UnicodeDecodeError:
                        pass
                mp4file.close()
            print("Temps nécessaire : {}".format(time.time()-self.time_debut))
            d2d_tcp.close()

            # if len(QUEUE_CACHE) == 3:  # Fonctionnement de la FIFO a modifier
            #     to_delete, _ = QUEUE_CACHE[0]
            #     os.remove(tempfile.gettempdir() + "/" + to_delete + ".mp4")
            #     QUEUE_CACHE.pop(0)
            #     del ALL_TEMP_FILES[to_delete]
            #
            # insert((self.hash_id, payload["pop"]))

        elif "[D2D_RECEIVER]" in data_utf8:
            payload = eval(data_utf8.split("$")[1])
            # use of payload["port_dest"]
            d2d_tcp_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            d2d_tcp_connection.bind(('', payload["port_dest"]))
            d2d_tcp_connection.listen(1)
            d2d_tcp, _ = d2d_tcp_connection.accept()
            data = d2d_tcp.recv(4096)
            print(data)
            if "[FILE_REQUEST]" in data.decode("utf-8"):
                hash = data.decode("utf-8").split("$")[1]
                with open(tempfile.gettempdir() + "/" + hash + ".mp4", 'rb') as file_in:
                    f = file_in.read(1024)
                    while (f):
                        d2d_tcp.send(f)
                        f = file_in.read(1024)
                    d2d_tcp.send(b"[END]")
                file_in.close()

            d2d_tcp.close()

        else:
            print("[ERROR]")
            sys.exit(0)


def depadding(f,size):
    print("Size depadding : {}".format(size))
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
    ref = PROCESS_ENCODE + 1
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




def decode(all_files, to_decode, f3):
    """

    :param all_files: List containing decoding files
    :param f3: files that will be soon created
    :return: none
    """
    all_files.append(to_decode)
    encode(all_files, f3)
    depadding(f3, SIZE_FILE)

if __name__ == "__main__":

    HOST = "127.0.0.1"  # Must be changed with the real server IP address
    PORT = 25555
    BROADCAST_PORT = 40000
    DIR_TEMP_NAME = "PIRCaching"
    PROCESS_ENCODE = multiprocessing.cpu_count()

    ALL_TEMP_FILES = dict()
    QUEUE_CACHE = list()  # LIST which represents the cache from the less popular to the most one (tuple)
    SIZE_FILE = int()
    D2D_THREAD_LIST = list()
    pop_file = float()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    ip = client.getsockname()[0]

    if DIR_TEMP_NAME not in os.listdir(tempfile.gettempdir()):
        os.mkdir(tempfile.gettempdir() + '/' + DIR_TEMP_NAME)

    tempfile.tempdir = tempfile.gettempdir() + "/" + DIR_TEMP_NAME
    print(tempfile.gettempdir())

    for file in os.listdir(tempfile.gettempdir()):
        # QUEUE_CACHE.append((file.split(".")[0], 1))
        ALL_TEMP_FILES[file.split(".")[0]] = tempfile.gettempdir() + "/" + file

    print(QUEUE_CACHE)
    receive_broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    receive_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    receive_broadcast.bind(('', BROADCAST_PORT))

    try:
        plain_message = input("Fichier à télecharger : ")
        while(True and plain_message!='q'):
                hash = hashlib.md5()
                print(plain_message)
                hash.update(bytes(plain_message, "utf-8"))
                hashed_message = hash.hexdigest()
                print("Hash : {}".format(hashed_message))
                print("Your cache : {}".format(QUEUE_CACHE))
                adding_cache = hashed_message+"+"+str([id for (id,_) in QUEUE_CACHE])
                client.send(bytes(adding_cache, "utf-8"))

                decode_data = str()
                sending = False
                while (not sending):
                    try:
                        decode_data, addr = receive_broadcast.recvfrom(1024) #Receiving amount of sendings
                        if "[SENDINGS]" in decode_data.decode("utf-8"):
                            sending = True
                    except UnicodeDecodeError:
                        pass

                time_init = time.time()
                sending = eval(decode_data.decode("utf-8").split("$")[1])
                print("Amount of sending (client) : {}".format(sending))
                i = int()
                found = False
                while  i < sending and not found:
                    print("Sending")
                    is_readable = False
                    while(not is_readable):
                        try:
                            data, _ = receive_broadcast.recvfrom(1024)
                            decode_data = data.decode("utf-8")
                            if "FILES" in decode_data:
                                print("Received files")
                                is_readable = True

                        except UnicodeDecodeError:
                            pass

                    if is_readable:
                        if "[FILES_D2D]" in decode_data:
                            if ip in decode_data:
                                D2Dthread = D2DTCPThreading(tcp_connection=client,
                                                                hash_id= hashed_message,
                                                                time = time_init)
                                D2D_THREAD_LIST.append(D2Dthread)
                                D2Dthread.start()
                            i += 1
                            continue


                        print(decode_data)
                        xor_files = decode_data.split("$")[1]
                        decodable = True
                        xor_files = eval(xor_files)
                        for (file ,size, pop) in xor_files:
                            print("Hashed : {}".format(hashed_message))
                            print(file)
                            if file == hashed_message:
                                print("Receiving...size : {}".format(size))
                                SIZE_FILE = size
                                decode_xor_files = list()
                                # Possible to decode the file I asked for
                                if len(xor_files) != 1:
                                    decode_xor_files = copy.deepcopy(xor_files)
                                    decode_xor_files.remove((file,size,pop))
                                    cached_file = os.listdir(tempfile.gettempdir())
                                    for (file,_,_) in decode_xor_files:
                                        print("XOR_FILE : {}".format(decode_xor_files))
                                        print(cached_file)
                                        if not file+".mp4" in cached_file:
                                            decodable = False
                                            break

                                if decodable:
                                    with open(tempfile.gettempdir()+"/temporary.mp4", "wb") as mp4file:
                                        while (True):
                                            data,_ = receive_broadcast.recvfrom(1024)
                                            mp4file.write(data)
                                            if len(data) != 1024:
                                                print("Fin de transmission")
                                                break

                                        mp4file.close()
                                    pop_file = pop
                                    if len(xor_files) == 1:
                                        os.rename(tempfile.gettempdir() + "/temporary.mp4",
                                                  tempfile.gettempdir() + "/" + hashed_message + ".mp4")
                                        print("Temps pris pour réception fichier : {}".format((time.time()-time_init)))
                                    else:
                                        decode([ALL_TEMP_FILES[file] for (file,_,_) in decode_xor_files] ,tempfile.gettempdir()+"/temporary.mp4", tempfile.gettempdir()+"/"+ hashed_message+".mp4")
                                        print("Temps pris pour réception fichier : {}".format((time.time()-time_init)))
                                        os.remove(tempfile.gettempdir()+"/temporary.mp4") #So far we'll remove this temporary file


                    i += 1
                for D2D_THREAD in D2D_THREAD_LIST:
                    if D2D_THREAD.is_alive():
                        print("Still one working thread")
                        D2D_THREAD.join()
                plain_message = input("Fichier à télecharger : ")

                if len(QUEUE_CACHE) == 3:  # Fonctionnement de la FIFO a modifier
                    print("QUEUE CACHE : {}".format(QUEUE_CACHE))
                    to_delete, _ = QUEUE_CACHE[0]
                    os.remove(tempfile.gettempdir() + "/" + to_delete + ".mp4")
                    QUEUE_CACHE.pop(0)
                    del ALL_TEMP_FILES[to_delete]

                insert((hashed_message, pop_file))
                ALL_TEMP_FILES[hashed_message] = tempfile.gettempdir() + "/" + hashed_message + ".mp4"

    except KeyboardInterrupt:
        print("Quitting...")
        sys.exit(0)
