import time
import os
import copy
import shutil

def padding(f1,f2):
    dif = os.stat(f2).st_size-os.stat(f1).st_size
    tab = bytearray(abs(dif))
    for i in range(abs(dif)):
        tab[i]=0

    file2 = open(f1 , 'ab+')
    file2.write(tab)
    file2.close()

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
    t_debut = time.time()
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
            for file in byte_list:
                result[byte1] ^= file[byte1]
        file_out.write(result)

    for f in list_file:
        f.close()
    temp_file_list.pop()
    print("Temp file lisr : {}".format(temp_file_list))
    for file in temp_file_list:
        os.remove(file)
    print("Fin encode : {}".format(time.time()-t_debut))


encode(["C:/Users/matth/PycharmProjects/PIR/videos/BETTER.mp4", "C:/Users/matth/PycharmProjects/PIR/videos/PSYCHO.mp4"],
       "C:/Users/matth/PycharmProjects/PIR/videos/sending.mp4")
