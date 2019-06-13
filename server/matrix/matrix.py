filexor=dict()
def MatrixDifRequeste(matrix, fileid):
    tab = list()
    for i in range(len(matrix)):
        filexor[fileid[i]] = list()
        for j in range(len(matrix[0])):
            if (i + j + 1) == len(matrix) or fileid[i + j + 1] == len(matrix[0]):
                break

            if matrix[i][fileid[i + j + 1]] == matrix[i + j + 1][fileid[i]] == 1:
                filexor[fileid[i]].append(fileid[i + j + 1])
    print(filexor)
    return filexor


def RequestIsRelatif(file):
    values = list()
    for val in file.values():
        if val != []:
            values.append(val)
    if len(values) == 0:
        return False
    return True


# Trouver l'origine du fichier choisi
def SearchOrigin(tab, c):
    list=tab
    print("Tab : {}".format(tab))
    print(" C : {}".format(c))
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            print(tab[i])
            if tab[i][1] == c:
                return list[i]


# Verifier si un element dans le liste
def SearchElement(tab, c):
    for i in range(len(tab)):
        if tab[i] == c:
            return True


# Traitement une liste de tous les xor de 2 fichiers, pour trouver des XOR de plusieurs fichiers
def TraitementXOR(file):
    keys = list(file.keys())
    temp = list()
    resultat = list()
    check = list()
    c = 0

    for j in keys:
        if j not in check:
            del check[:]
            for value in file[j]:
                check.append(value)
                temp.append([j, value])
                resultat.append([j, value])
            for i in check:
                for val in file[i]:
                    if val in check:
                        t=list()
                        print(resultat)
                        #c = resultat.index(SearchOrigin(temp, i))
                        if SearchOrigin(temp, i).append(val)!=None:
                         t=SearchOrigin(temp,i)
                         resultat.append(t.append(val))
                    else:
                        check.append(val)
                        temp.append([i, val])
                        resultat.append([i, val])
    return resultat


# Sort une liste desc
def sorte(list):
    list.sort(key=lambda x: len(x), reverse=True)
    return list


# Trouver des ensembles de XOR possible
def XORfinal(list):
    sorte(list)
    liste = []
    liste.append(list[0])
    for j in range(len(list)):
        c = 0
        for i in range(len(liste)):
            if liste[i] != list[j]:
                if len(set(liste[i] + list[j])) == (len(liste[i]) + len(list[j])):
                    c = c + 1
                if c == len(liste):
                    liste.append(list[j])
    sorte(liste)
    return liste


# Choisir un ensemble des XOR pour effectuer
def ChoixMsg(list, tab):
    print(list)
    for i in range(len(list)):
        for val in list[i]:
            if SearchElement(tab, val) == True:
                tab.remove(val)
    if len(tab) != 0:
        for val in tab:
            list.append([val])
    print(list)
    return list
