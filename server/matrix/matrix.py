def MatrixDifRequeste(matrix ,fileid):
    tab =list()
    filexor = dict()
    for i in range(len(matrix)):
        filexor[fileid[i] ] =list()
        for j in range(len(matrix[0])):
            if ( i + j +1 )==len(matrix) or fileid[ i + j +1 ]==len(matrix[0]):
                break

            if matrix[i][fileid[ i + j +1] ]==matrix[ i + j +1][fileid[i]]==1:

                filexor[fileid[i]].append(fileid[ i + j +1])
    print(filexor)
    return filexor

def RequestIsRelatif(file):
    values =list()
    for val in file.values():
        if val!=[]:
            values.append(val)
    if len(values )==0:
        return False
    return True


# Trouver l'origine du fichier choisi
def SearchOrigin(tab ,c):
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            if tab[i][1 ]==c:
                return tab[i]


# Verifier si un element dans le liste
def SearchElement(tab ,c):
    for i in range(len(tab)):
        if tab[i ]==c:
            return True


# Traitement une liste de tous les xor de 2 fichiers, pour trouver des XOR de plusieurs fichiers
def TraitementXOR(file):
    keys =list(file.keys())
    temp =list()
    resultat =list()
    check =list()
    c=0

    for j in keys:
        for value in file[j]:
            check.append(value)
            temp.append([j,value])
            resultat.append([j,value])
    for i in check:
        for val in file[i]:
            print(val)
            if val in check:
                c=resultat.index(SearchOrigin(temp,i))
                resultat[c].append(val)
                print(resultat)
            else:
                check.append(val)
                temp.append([i,val] )
                resultat.append([i,val] )
    # print(resultat)
    return resultat



def sorte(list):
    list.sort(key=lambda x:len( x), reverse = True)
    return list


#



def XORfinal(list):
    sorte(list)
    liste=[]
    for i in range(len(list)):
        liste.append([list[i]])
        for j in range(i,len (list)):
            if list[i]!=list[j]:

                if len(set(list[i]+list[j]))==(len(list[i])+len(list[j])):
                    liste[i].append(list[j])
    sorte(liste)
    del liste[1:]
        # S  eulement maintenant apres ajouter fonction travail avec la cache pour trouver des msg correspond le plus possible

    return liste


#


#hoisir un ensemble des XOR pour effectuer
def ChoixMsg(list,tab ):
    for i in range(len(list[0])):
        for val in list[0][i]:
            if SearchElement(tab,val )==True:
                tab.remove(val)
    if len(tab)!=0 :
        for val in tab:
            list[0].append([val])
    print(list[0])
    return list[0]