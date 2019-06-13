import threading
import socket
import sys
import os

def insert(tuple, queue):
    hash,pop = tuple
    for (queue_hash, queue_pop) in queue:
        if pop < queue_pop:
                return queue.insert(queue.index((queue_hash, queue_pop)), (hash,pop))
    return queue.append((hash,pop))


class D2DTCPThreading(threading.Thread):

    def __init__(self, tcp_connection, hash_id, temp_dir, queue_file, all_temp_files):
        threading.Thread.__init__(self)
        self.tcp_connection = tcp_connection
        self.hash_id = hash_id
        self.temp_dir = temp_dir
        self.queue_file = queue_file
        self.all_temp_files = all_temp_files

    def run(self):
        data,_ = self.tcp_connection.listen(4096)
        data_utf8 = data.decode("utf-8")
        if "[D2D_SENDER]" in data_utf8:
            amount_of_try = 5
            payload = eval(data_utf8.split("$")[1])[0]
            d2d_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            d2d_tcp.bind(('', payload["ip_src"]))

            while (amount_of_try >=0):
                try:
                    d2d_tcp.connect((payload["ip_dest"], payload["port_dest"]))
                    break
                except socket.error:
                    print("Error trying again to initialize connection")
                    if amount_of_try == 0:
                        print("Can no longer succed")
                        sys.exit(0)
            message = "[FILE_REQUEST]${}".format(self.hash_id)
            d2d_tcp.send(bytes(message, "utf-8"))

            with open(self.temp_dir + "/"+self.hash_id+".mp4", "wb") as mp4file:
                while (True):
                    data, _ = d2d_tcp.recv(1024)
                    mp4file.write(data)
                    if len(data) != 1024:
                        break
                mp4file.close()        
            d2d_tcp.close()

            if len(self.queue_file) == 3:  # Fonctionnement de la FIFO a modifier
                to_delete, _ = self.queue_file[0]
                os.remove(self.temp_dir + "/" + to_delete + ".mp4")
                self.queue_file.pop(0)
                del self.all_temp_files[to_delete]
             
            insert((self.hash_id, payload["pop"]), self.queue_file)

        elif "[D2D_RECEIVER]" in data_utf8:
            payload = eval(data_utf8.split("$")[1])[0]
            # use of payload["port_dest"]
            d2d_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            d2d_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            d2d_tcp.bind(('', payload["port_dest"]))

            data = d2d_tcp.recv(1024)
            if "[FILE_REQUEST]" in data.decode("utf-8"):
                hash = data.decode("utf-8").split("$")[1]
                with open(self.temp_dir+"/"+hash+".mp4", 'rb') as file_in:
                    f = file_in.read(1024)
                    while (f):
                        d2d_tcp.send(f)
                        f = file_in.read(1024)
                file_in.close()

            d2d_tcp.close()

        else:
            print("[ERROR]")
            sys.exit(0)