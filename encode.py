#!/usr/bin/env python
# coding: utf-8
import os
from functools import partial
import base64
import time

def padding(f1,f2):
    dif = os.stat(f1).st_size-os.stat(f2).st_size
    tab = bytearray(abs(dif))
    for i in range(abs(dif)):
        tab[i]=0
    if dif == 0:
        return(0)
    if dif >0:
        file2 = open(f2, 'ab+')
        file2.write(tab)
        file2.close()
    else:
        file1 = open(f1, 'ab+')
        file1.write(tab)
        file1.close()
    print(os.stat(f1).st_size-os.stat(f2).st_size)

def encode(f1,f2,f3):
        padding(f1,f2)
        size = os.stat(f1).st_size
        result=bytearray(size)
        with open(f1, 'rb') as file1:
            with open(f2, 'rb') as file2:
                with open(f3, 'wb') as file_out:
                    fi1=bytearray(file1.read())
                    fi2=bytearray(file2.read())
                    for byte1 in range(size):
                        result[byte1]=(fi1[byte1]^fi2[byte1])
                    file_out.write(result)
                    return file_out



def main():
    encode("/mnt/c/Users/Allan GOUDJI/Downloads/PIR/test1.mp4","/mnt/c/Users/Allan GOUDJI/Downloads/PIR/test2.mp4","/mnt/c/Users/Allan GOUDJI/Downloads/PIR/testf.txt")
    encode("/mnt/c/Users/Allan GOUDJI/Downloads/PIR/testf.txt", "/mnt/c/Users/Allan GOUDJI/Downloads/PIR/test1.mp4","/mnt/c/Users/Allan GOUDJI/Downloads/PIR/test21.mp4")
    encode("/mnt/c/Users/Allan GOUDJI/Downloads/PIR/testf.txt", "/mnt/c/Users/Allan GOUDJI/Downloads/PIR/test2.mp4","/mnt/c/Users/Allan GOUDJI/Downloads/PIR/test11.mp4")
main()
