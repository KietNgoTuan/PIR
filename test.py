import os
import copy
import shutil
import multiprocessing

# PROCESS_ENCODE = multiprocessing.cpu_count()
PROCESS_ENCODE = multiprocessing.cpu_count()
lock_result = multiprocessing.Lock()



def encode_data(debut,fin,result, ns):
    print("Longueur tab : {}".format(len(ns)))
    for byte in range(debut,fin):
        # for file in ns.bytelist:
        #     result[byte] ^= file[byte]
        pass


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


def get_all_frag_threading(size, ref=PROCESS_ENCODE+1):
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
    if __name__ == "__main__":

        path , max_size = get_largest_file(all_files)
        result = multiprocessing.Array('b', max_size)
        list_file = list()
        for each_path in all_files:
            f = open(each_path, 'rb')
            list_file.append(f)
        process_list = list()
        bytelist = list()
        manager = multiprocessing.Manager()
        ns = manager.Namespace()
        print(PROCESS_ENCODE)
        with open(f3, 'wb') as file_out:
            for each_elt in range(len(all_files)):
                bytelist.append(bytearray(list_file[each_elt].read()))
            frag = get_all_frag_threading(max_size)
            print(frag)
            i= 0
            while i < len(frag)-1:
                temp_list = list()
                for elt in bytelist:
                    try:
                        _ = elt[frag[i+1]-1]
                        print((frag[i],frag[i+1]))
                        temp_list.append(elt[frag[i]:frag[i+1]])
                    except IndexError:
                        print("Problème d'index")
                        pass
                ns.bytelist = temp_list
                print(len(ns.bytelist))
                p = multiprocessing.Process(
                    target = encode_data,
                    args = (frag[i],frag[i+1],result,ns.bytelist)
                )
                process_list.append(p)
                p.start()
                i += 1

        for p in process_list:
            p.join()
        # print(result[:])
        # file_out.write(result[:])

        for f in list_file:
            f.close()


encode(["C:/Users/matth/PycharmProjects/PIR/videos/APPLE.mp4", "C:/Users/matth/PycharmProjects/PIR/videos/RINGTONE.mp4"],
"C:/Users/matth/PycharmProjects/PIR/videos/sending.mp4")