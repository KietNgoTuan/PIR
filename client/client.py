import socket
import os
import hashlib
import tempfile
import time
import sys
import shutil
import copy

HOST ="127.0.0.1" # Must be changed with the real server IP address
PORT=25555
BROADCAST_PORT = 40000
DIR_TEMP_NAME = "PIRCaching"
ALL_TEMP_FILES = dict()
QUEUE_CACHE = list() # LIST which represents the cache from the oldest to the newest
SIZE_FILE = int()

client= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST,PORT))
client.settimeout(1)

if DIR_TEMP_NAME not in os.listdir(tempfile.gettempdir()):
    os.mkdir(tempfile.gettempdir()+'/'+DIR_TEMP_NAME)

tempfile.tempdir = tempfile.gettempdir()+"/"+DIR_TEMP_NAME
print(tempfile.gettempdir())

"""
Code to check all files stored in temp memory
"""

def insert(file):
    global QUEUE_CACHE
    for i in range(len(QUEUE_CACHE)):
        if (time.ctime(os.path.getmtime(tempfile.gettempdir()+"/"+file)) <=
            time.ctime(os.path.getmtime(tempfile.gettempdir()+"/"+QUEUE_CACHE[i]))):
                return QUEUE_CACHE.insert(i, file)
    return QUEUE_CACHE.append(file)


for file in os.listdir(tempfile.gettempdir()):
    insert(file)
    ALL_TEMP_FILES[file.split(".")[0]] = tempfile.gettempdir()+"/"+file


receive_broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
receive_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
receive_broadcast.bind(('', BROADCAST_PORT))

hash = hashlib.md5()

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
    temp_file_list.pop()
    for file in temp_file_list:
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
            hash.update(bytes(plain_message, "utf-8"))
            hashed_message = hash.hexdigest()

            adding_cache = hashed_message+"+"+str(list(ALL_TEMP_FILES.keys()))
            client.send(bytes(adding_cache, "utf-8"))

            data, addr = receive_broadcast.recvfrom(1024)

            if "[FILES]" in data.decode("utf-8"):
                xor_files = data.decode("utf-8").split(":")[1].split("+")
                print(xor_files)
                xor_files.pop()
                for (file ,size) in xor_files:
                    if file == hashed_message:
                        SIZE_FILE = size



            with open(tempfile.gettempdir()+"/temporary.mp4", "wb") as mp4file:
                while (True):
                    data,_ = receive_broadcast.recvfrom(1024)
                    mp4file.write(data)
                    if len(data) != 1024:
                        print("Fin de transmission")
                        break


                mp4file.close()
                if len(QUEUE_CACHE) == 3: # Fonctionnement de la FIFO
                    os.remove(tempfile.gettempdir()+"/"+QUEUE_CACHE[0])
                    QUEUE_CACHE.pop(0)

                QUEUE_CACHE.append(hashed_message+"mp4") #So far file is always saved
                decode([ALL_TEMP_FILES["105423efc7504e3768979ae5e3c0f255"], ALL_TEMP_FILES["e21ec0e7dbfbe757e0930f95a077b434"]] ,tempfile.gettempdir()+"/temporary.mp4", tempfile.gettempdir()+"/"+ hashed_message+".mp4")
                os.remove(tempfile.gettempdir()+"/temporary.mp4") #So far we'll remove this temporary file
            plain_message = input("Fichier à télecharger : ")
    print('You are now disconnected')

except KeyboardInterrupt:
    print("Quitting...")
    sys.exit(0)
    # ALL_TEMP_FILES[hashed_message] = tempfile.gettempdir()+hashed_message+".mp4"

    # if(data.decode('utf-8') != "File not found" and data != str()):
    #     data = data.decode('utf-8').split("+")
    #     full_data += data[1].split(":")[1]
    #     print(full_data)
    #     print(data[0].split(":")[1])
    #     print(data[1].split(":")[1])
    #     cache.set(message, data[1].split(":")[1])
    #     print(cache.get(message))



