import os
import copy
import shutil
import multiprocessing

# PROCESS_ENCODE = multiprocessing.cpu_count()
PROCESS_ENCODE = 1
lock_result = multiprocessing.Lock()



def encode_data(debut,fin,result, ns):
    print("Lancement thread")
    print(debut)
    print(fin)
    print(type(ns.bytelist))
    for byte in range(debut,fin):
        print(byte)
        for file in ns.bytelist:
            result[byte] ^= file[byte]


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

def padding(f1,f2):
    dif = os.stat(f2).st_size-os.stat(f1).st_size
    tab = bytearray(abs(dif))
    for i in range(abs(dif)):
        tab[i]=0

    file2 = open(f1 , 'ab+')
    file2.write(tab)
    file2.close()

def get_all_frag_threading(size, ref=PROCESS_ENCODE):
    size_list = list()
    value = 0
    for i in range(ref):
        if i == ref-1:
            size_list.append(size)
            return size_list
        value += int(size/ref)
        size_list.append(value)



def encode(all_files, f3):
    """
    :param all_files: all files that must be XOR together
    :param f3: outfile
    :return: outfile
    """
    if __name__ == "__main__":

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
        print("Before...")
        result = multiprocessing.Array('b', max_size)
        print("After")
        list_file = list()
        for each_path in temp_file_list:
            f = open(each_path, 'rb')
            list_file.append(f)
        process_list = list()
        print("Manager before")
        manager = multiprocessing.Manager()
        ns = manager.Namespace()
        print("After")
        ns.bytelist = list()
        print(PROCESS_ENCODE)
        with open(f3, 'wb') as file_out:
            for each_elt in range(len(all_files)):
                ns.bytelist.append(bytearray(list_file[each_elt].read()))
            frag = get_all_frag_threading(max_size)
            # for i in range(len(frag)-1):
            # p = multiprocessing.Process(
            #     target = encode_data,
            #     args = (frag[i],frag[i+1],result,ns)
            # )
            p = multiprocessing.Process(
                target=encode_data,
                args=(0, max_size, result, ns,)
            )
            p.start()
            process_list.append(p)
        for p in process_list:
            p.join()

            file_out.write(result)

        for f in list_file:
            f.close()
        temp_file_list.pop()
        print("Temp file list : {}".format(temp_file_list))
        for file in temp_file_list:
            os.remove(file)

encode(["C:/Users/matth/PycharmProjects/PIR/videos/APPLE.mp4", "C:/Users/matth/PycharmProjects/PIR/videos/RINGTONE.mp4"],
"C:/Users/matth/PycharmProjects/PIR/videos/sending.mp4")