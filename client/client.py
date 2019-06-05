import socket
import os
import hashlib
import tempfile
import time
import sys
import shutil

HOST ="127.0.0.1" # Must be changed with the real server IP address
PORT=25555
BROADCAST_PORT = 40000
DIR_TEMP_NAME = "PIRCaching"
ALL_TEMP_FILES = dict()
QUEUE_CACHE = list() # LIST which represents the cache from the oldest to the newest


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
    # ------------------------------------------ #
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



def decode(f1,f2,f3):
    fi=open(f1,"rb")
    temp=fi.read()[:32]
    print("Temp : {}".format(temp))
    tab=temp.decode()
    print("Tab : {}".format(tab))
    print(int(tab,2))
    fi.close()
    size= int(tab,2)
    couper(f1,32)
    #-------------------------------------------#
    dif=os.stat(f1).st_size-os.stat(f2).st_size
    print(os.stat(f1).st_size)
    print(os.stat(f2).st_size)
    if dif>0:
        encode(f1,f2,f3)
        depadding(f2,dif)

    else:
        encode(f1,f2,f3)
        depadding(f3,min(os.stat(f1).st_size, os.stat(f2).st_size))

    couper(f3, 32)

try:
    plain_message = input("Fichier à télecharger : ")
    while(True and plain_message!='q'):
            hash.update(bytes(plain_message, "utf-8"))
            hashed_message = hash.hexdigest()

            adding_cache = hashed_message+"+"+str(list(ALL_TEMP_FILES.keys()))
            client.send(bytes(adding_cache, "utf-8"))

            data, addr = receive_broadcast.recvfrom(1024)
            with open(tempfile.gettempdir()+"/temporary.mp4", "wb") as mp4file:
                while (True):
                    mp4file.write(data)
                    if len(data) != 1024:
                        print("Fin de transmission")
                        break

                    data,_ = receive_broadcast.recvfrom(1024)

                mp4file.close()
                decode(tempfile.gettempdir()+"/temporary.mp4", ALL_TEMP_FILES["105423efc7504e3768979ae5e3c0f255"], tempfile.gettempdir()+"/finaly_file.mp4")
            # os.remove(tempfile.gettempdir()+"/temporary.mp4")
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



