import socket
import os
import hashlib
import tempfile

HOST ="127.0.0.1" # Must be changed with the real server IP address
PORT=25555
BROADCAST_PORT = 40000
DIR_TEMP_NAME = "PIRCaching"
ALL_TEMP_FILES = dict()


client= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST,PORT))
client.settimeout(1)
full_data = str()


if DIR_TEMP_NAME not in os.listdir(tempfile.gettempdir()):
    print(tempfile.gettempdir())
    os.mkdir(tempfile.gettempdir()+'/'+DIR_TEMP_NAME)

tempfile.tempdir = tempfile.gettempdir()+"/"+DIR_TEMP_NAME
print(tempfile.gettempdir())

"""
Code to check all files stored in temp memory
"""

for file in os.listdir(tempfile.gettempdir()):
    ALL_TEMP_FILES[file.split(".")[0]] = tempfile.gettempdir()+"/"+file

print(ALL_TEMP_FILES)

receive_broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
receive_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
receive_broadcast.bind(('', BROADCAST_PORT))
receive_broadcast.settimeout(1)

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
    smallsize = padding(f1, f2)
    s = "%032d" % int(bin(smallsize)[2:])
    tabsize = bytearray(s.encode())
    size = os.stat(f1).st_size
    result = bytearray(size)
    with open(f1, 'rb') as file1:
        with open(f2, 'rb') as file2:
            with open(f3, 'wb') as file_out:
                fi1 = bytearray(file1.read())
                fi2 = bytearray(file2.read())
                for byte1 in range(size):
                    result[byte1] = (fi1[byte1] ^ fi2[byte1])
                if smallsize == 0:
                    tab = result
                else:
                    tab = tabsize + result
                file_out.write(tab)
                print(os.stat(f3).st_size)
                return f3


def decode(f1,f2,f3):
    fi=open(f1,"rb")
    temp=fi.read()[:32]
    tab=temp.decode()
    print(int(tab,2))
    fi.close()
    size= int(tab,2)
    couper(f1,32)
    dif=os.stat(f1).st_size-os.stat(f2).st_size
    print(os.stat(f1).st_size)
    print(os.stat(f2).st_size)
    if dif>0:
        padding(f1,f2)
        encode(f1,f2,f3)
        depadding(f2,dif)
        print("dsd")
    else:
        encode(f1,f2,f3)
        depadding(f3,size)
        print("sss")
# try:
#     def __run__cache():
#         subprocess.call("..\memcached\memcached.exe")
#
#     thread = threading.Thread(target =__run__cache)
#     thread.start()
#
# except subprocess.CalledProcessError:
#     sys.exit(-1)
#
# print("Defining cache")
# cache = memcache.Client(["127.0.0.1:11211"], debug=0)

while(True):
    plain_message = input("Fichier à télecharger : ")
    hash.update(bytes(plain_message, "utf-8"))
    hashed_message = hash.hexdigest()

    if hashed_message in ALL_TEMP_FILES:
        print("Got it in cache")
    else:
        adding_cache = hashed_message+"+"+str(list(ALL_TEMP_FILES.keys()))
        client.send(bytes(adding_cache, "utf-8"))

        data, addr = receive_broadcast.recvfrom(4096)
        print(data)
        # with open(tempfile.gettempdir()+"/"+hashed_message+".mp4", "wb") as mp4file:
        #     while (True):
        #         mp4file.write(data)
        #         try:
        #             data,_ = receive_broadcast.recvfrom(1024)
        #             full_data += len(data)
        #         except socket.timeout:
        #             receive_broadcast.close()
        #             break
        #     mp4file.close()

        while True:
            try:
                full_data += len(data)
                data = receive_broadcast.recvfrom(4096)
            except socket.timeout:
                break

        print(len(full_data))
        # print(len(full_data))
        # print("All data received")
        # temp = tempfile.NamedTemporaryFile(prefix=hashed_message+'\'', suffix="", delete=False)
        # temp.write(bytes(full_data, "utf-8"))
        ALL_TEMP_FILES[hashed_message] = tempfile.gettempdir()+hashed_message+".mp4"

    # if(data.decode('utf-8') != "File not found" and data != str()):
    #     data = data.decode('utf-8').split("+")
    #     full_data += data[1].split(":")[1]
    #     print(full_data)
    #     print(data[0].split(":")[1])
    #     print(data[1].split(":")[1])
    #     cache.set(message, data[1].split(":")[1])
    #     print(cache.get(message))



