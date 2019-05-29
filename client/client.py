import socket as s
import os
import subprocess
import sys
import memcache
import threading
import tempfile

HOST ="127.0.0.1" # Must be changed with the real server IP address
PORT=25555
DIR_TEMP_NAME = "PIRCaching"

client= s.socket(s.AF_INET,s.SOCK_STREAM)
client.connect((HOST,PORT))
client.settimeout(1)
full_data = str()


if DIR_TEMP_NAME not in os.listdir(tempfile.gettempdir()):
    print(tempfile.gettempdir())
    os.mkdir(tempfile.gettempdir()+'/'+DIR_TEMP_NAME)
    print("Done")

tempfile.tempdir = tempfile.gettempdir()+"/"+DIR_TEMP_NAME
print(tempfile.gettempdir())

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
    message = input("Fichier à télecharger : ")
    if message == str():
        print("Got it in cache")
    else:

        client.send(message.encode('utf-8'))
        data = client.recv(4096)

        while (True):
            full_data += str(data)
            try:
                data = client.recv(4096)
            except s.timeout:
                break


        print("All data received")
        print(full_data.split("key:")[1])
        temp = tempfile.TemporaryFile(prefix=full_data.split("key:")[1], suffix="")
        temp.write(bytes(full_data.split("key:")[0], "utf-8"))

    # if(data.decode('utf-8') != "File not found" and data != str()):
    #     data = data.decode('utf-8').split("+")
    #     full_data += data[1].split(":")[1]
    #     print(full_data)
    #     print(data[0].split(":")[1])
    #     print(data[1].split(":")[1])
    #     cache.set(message, data[1].split(":")[1])
    #     print(cache.get(message))



