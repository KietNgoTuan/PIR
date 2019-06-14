import socket
import os
import hashlib
import tempfile
import time
import sys
import shutil
import copy
import threading

HOST ="192.168.1.42" # Must be changed with the real server IP address
PORT=25555
BROADCAST_PORT = 40000
DIR_TEMP_NAME = "PIRCaching"
ALL_TEMP_FILES = dict()
QUEUE_CACHE = list() # LIST which represents the cache from the less popular to the most one (tuple)
SIZE_FILE = int()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST,PORT))
client.settimeout(1)
ip = client.getsockname()[0]

if DIR_TEMP_NAME not in os.listdir(tempfile.gettempdir()):
    os.mkdir(tempfile.gettempdir()+'/'+DIR_TEMP_NAME)

tempfile.tempdir = tempfile.gettempdir()+"/"+DIR_TEMP_NAME
print(tempfile.gettempdir())

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


for file in os.listdir(tempfile.gettempdir()):
    # QUEUE_CACHE.append((file.split(".")[0], 1))
    ALL_TEMP_FILES[file.split(".")[0]] = tempfile.gettempdir()+"/"+file

print(QUEUE_CACHE)
receive_broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
receive_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
receive_broadcast.bind(('', BROADCAST_PORT))

"""
    Utilisation du module D2D
"""


class D2DTCPThreading(threading.Thread):

    def __init__(self, tcp_connection, hash_id):
        threading.Thread.__init__(self)
        self.tcp_connection = tcp_connection
        self.hash_id = hash_id

    def run(self):
        data = self.tcp_connection.recv(4096)
        data_utf8 = data.decode("utf-8")
        print(data_utf8)
        if "[D2D_SENDER]" in data_utf8:
            amount_of_try = 5
            payload = eval(data_utf8.split("$")[1])
            d2d_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
                    data, _ = d2d_tcp.recv(1024)
                    mp4file.write(data)
                    if len(data) != 1024:
                        break
                mp4file.close()
            d2d_tcp.close()

            if len(QUEUE_CACHE) == 3:  # Fonctionnement de la FIFO a modifier
                to_delete, _ = QUEUE_CACHE[0]
                os.remove(tempfile.gettempdir() + "/" + to_delete + ".mp4")
                QUEUE_CACHE.pop(0)
                del ALL_TEMP_FILES[to_delete]

            insert((self.hash_id, payload["pop"]))

        elif "[D2D_RECEIVER]" in data_utf8:
            payload = eval(data_utf8.split("$")[1])
            # use of payload["port_dest"]
            d2d_tcp_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            d2d_tcp_connection.bind(('', payload["port_dest"]))
            d2d_tcp_connection.listen(1)
            self.tcp_connection.write(b"[READY_D2D]")
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
                file_in.close()

            d2d_tcp.close()

        else:
            print("[ERROR]")
            sys.exit(0)



def padding(f1,f2):
    dif = os.stat(f2).st_size-os.stat(f1).st_size
    tab = bytearray(abs(dif))
    for i in range(abs(dif)):
        tab[i]=0

    file2 = open(f1 , 'ab+')
    file2.write(tab)
    file2.close()


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

def encode(all_files, f3):
    """
    :param all_files: all files that must be XOR together
    :param f3: outfile
    :return: outfile
    """
    print(all_files)
    path, max_size = get_largest_file(all_files)
    print(path)
    print(max_size)
    temp_list = copy.deepcopy(all_files)
    print(temp_list)
    temp_list.remove(path)
    print(temp_list)
    temp_file_list = list()

    for each_path in range(len(temp_list)):
        temp_file = os.getcwd() + "/temp_file/" + temp_list[each_path].split("/")[-1].split(".")[0] + "_temp.mp4"
        temp_file_list.append(temp_file)
        print(temp_file_list)
        shutil.copyfile(temp_list[each_path], temp_file_list[each_path], follow_symlinks=True)
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
    for file in temp_file_list:
        if "_temp" in file:
            os.remove(file)


def decode(all_files, to_decode, f3):
    """

    :param all_files: List containing decoding files
    :param f3: files that will be soon created
    :return: none
    """
    all_files.append(to_decode)
    encode(all_files, f3)
    depadding(f3, SIZE_FILE)

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
                                                            hash_id= hashed_message)
                            D2Dthread.start()
                            if ip == decode_data.split("$")[1].split("->")[0]:
                                D2Dthread.join()
                                break
                            i += 1
                            continue
                        else:
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

                                if len(xor_files) == 1:
                                    os.rename(tempfile.gettempdir() + "/temporary.mp4",
                                              tempfile.gettempdir() + "/" + hashed_message + ".mp4")
                                    print("Temps pris pour réception fichier : {}".format((time.time()-time_init)))
                                else:
                                    decode([ALL_TEMP_FILES[file] for (file,_,_) in decode_xor_files] ,tempfile.gettempdir()+"/temporary.mp4", tempfile.gettempdir()+"/"+ hashed_message+".mp4")
                                    print("Temps pris pour réception fichier : {}".format((time.time()-time_init)))
                                    os.remove(tempfile.gettempdir()+"/temporary.mp4") #So far we'll remove this temporary file


                                if len(QUEUE_CACHE) == 3:  # Fonctionnement de la FIFO a modifier
                                    print("QUEUE CACHE : {}".format(QUEUE_CACHE))
                                    to_delete,_ = QUEUE_CACHE[0]
                                    os.remove(tempfile.gettempdir() + "/" + to_delete+".mp4")
                                    QUEUE_CACHE.pop(0)
                                    del ALL_TEMP_FILES[to_delete]

                                insert((hashed_message,pop))
                                ALL_TEMP_FILES[hashed_message] = tempfile.gettempdir()+"/"+hashed_message+".mp4"
                i += 1
            plain_message = input("Fichier à télecharger : ")

except KeyboardInterrupt:
    print("Quitting...")
    sys.exit(0)
