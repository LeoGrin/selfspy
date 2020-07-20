import re
import pandas as pd
import numpy as np

#############
# When we see a backspace pressed we want to know :
#       1) what was the erased key ?
#       2) what was the replaced key ? (the key you were supposed to type)

# Notes :

# Careful with inversion :
# ..s<[Backspace]>ts is probably a inversion of t and s and not simply "t instead of s"

# Careful with number of backspace:
# <[Backspace]x2> should be dealt with

# Careful with other command:
# <[Alt : Backspace]> count as a backspace
# but <Left><Enter><[Backspace]> makes it hard to know what was the erased letter : this backspace should not be counted



#############

# TODO : improve it to check if there is an error anywhere in the deleted text (right now we only look at the last letter)
# check distance betweeen the deleted word and the replaced word : if it's too big doesn't count. And look at all the diff
# Related : take into account the case where spirt<[Backspace]x5>port (count as an unnecessary backspace now, but there aren't too many)
# TODO : take into account clicks
# TODO : I've just noticed in selfstats row.decrypt_keys() instead of row.decrypt_text(), which gives directly a list of keys pressed.
# Are we sure regex are still the best solution with this function ??

def sorted_unique(array, n=10):
    """"sort the unique element of an array by count, and display the nth first"""
    n = min(n, len(array))
    ar, count = np.unique(array, return_counts=True)
    indices = np.argsort(-count)
    return ar[indices][:n], count[indices][:n]

def display_typing_quality(dic, n=15):
    """
    Display typing quality statistics for selfstats
    :param dic: dic of the form {l_deleted, l_replaced, l_coupled, l_inversion, n_unnecessary}
    :return: None
    """
    print("{} unnecessary backspace".format(dic["n_unnecessary"]))
    print("{} inverted letters (e.g ts instead of st)".format(len(dic["l_inversion"])))
    print("{} deleted letters (excluding unnecessary backspace and inversions)".format(len(dic["l_deleted"])))
    print
    print("Most missed keys (excluding inversions): ")
    keys, counts = sorted_unique(dic["l_replaced"], n)
    for i in range(len(keys)):
        print(u"Key : {} ({} times)".format(keys[i], counts[i]))
    print
    print("Keys you most type instead of another (excluding inversions): ")
    keys, counts = sorted_unique(dic["l_coupled"], n)
    for i in range(len(keys)):
        print(u"Keys : {} instead of {} ({} times)".format(keys[i][0], keys[i][1], counts[i]))
    print
    print("Keys you most invert (e.g ts instead of st): ")
    keys, counts = sorted_unique(dic["l_inversion"], n)
    for i in range(len(keys)):
        print(u"Keys : {} instead of {} ({} times)".format(keys[i][0] + keys[i][1], keys[i][1] + keys[i][0], counts[i]))


def create_dic():
    """
    Create the dictionnary which stores the results of key_around_backspace. Useful to make change easier while leaving
     selfstats code intact.
    :return: the created dictionnary
    """
    dic = {"l_deleted": [], "l_replaced": [], "l_coupled": [], "l_inversion": [], "n_unnecessary": 0}

    return dic


def update_dic(dic, text):
    """
    :param dic:  dic of the form {l_deleted, l_replaced, l_coupled, l_inversion, n_unnecessary}
    :param text: new text to analysie
    :return: the updated dictionnary
    """
    l_deleted_new, l_replaced_new, l_coupled_new, l_inversion_new, n_unnecessary_new = keys_around_backspace(text)

    dic["l_deleted"].extend(l_deleted_new)
    dic["l_replaced"].extend(l_replaced_new)
    dic["l_coupled"].extend(l_coupled_new)
    dic["l_inversion"].extend(l_inversion_new)
    dic["n_unnecessary"] += n_unnecessary_new

    return dic

def unnecessary_backspace(key_deleted, s_right):
    return s_right[0] == key_deleted

def inversion_1_backspace(key_deleted, s_right):
    """check if there's no inversion : "st" instead of "ts", that is "s<[Backspace]>ts (only for 1 backspace) and return the inverted letters"""
    if len(s_right) <= 1:
        return False, ''
    return s_right[1] == key_deleted and s_right[0] != key_deleted, key_deleted + s_right[0]

def inversion_more_backspace(s_left, n_backspace, s_right):
    """check if there's no inversion : "st" instead of "ts", that is "st<[Backspace]x2>ts (only for 2 or more backspaces) and return the inverted letters"""
    if len(s_right) <= 1:
        return False, ''
    return s_left[-n_backspace] == s_right[1] and s_left[-n_backspace + 1] == s_right[0], s_right[1] + s_right[0]


def keys_around_backspace(s):
    match_1_backspace = re.findall("([^\>])\<\[[^\]]*Backspace\]\>([^\<]+)(?:\<|\Z)", s) # match jfksdfj<[Backspace]>jdskjd and return the erased letter and the replacement text
    match_more_backpace = re.findall("(?:\A|\>)([^\>]+)\<\[[^\]]*Backspace\]x(\d*)\>([^\<]+)(?:\<|\Z)", s)# match dfdfkl<[Backspace]x2>kjkfkdjf etc. and return the erased letter and the replacement text
    l_deleted, l_replaced, l_coupled, l_inversion = [], [], [], []
    n_unnecessary = 0
    if match_1_backspace:
        for group in match_1_backspace:
            key_deleted, s_right = group
            key_replaced = s_right[0]
            #is_inversion = inversion(key_deleted, s_right)
            is_inversion, inverted_letters = inversion_1_backspace(key_deleted, s_right)
            # check if there's no inversion ("st" instead of "ts", that is "s<[Backspace]>ts"
            if is_inversion:
                l_inversion.append(inverted_letters)
            elif unnecessary_backspace(key_deleted, s_right):
                n_unnecessary += 1
            else:
                l_deleted.append(key_deleted)
                l_replaced.append(key_replaced)
                l_coupled.append(key_deleted + key_replaced)

    if match_more_backpace:
        for group in match_more_backpace:
            s_left, n_backspace, s_right = group
            n_backspace = int(n_backspace)
            if n_backspace <= len(s_left):
                key_deleted = s_left[-n_backspace]
                key_replaced = s_right[0]
                is_inversion, inverted_letters = inversion_more_backspace(s_left, n_backspace, s_right)
                # check if there's no inversion : "st" instead of "ts", that is "st<[Backspace]x2>ts
                if is_inversion:
                    l_inversion.append(inverted_letters)
                elif unnecessary_backspace(key_deleted, s_right):
                    n_unnecessary += 1
                else:
                    l_deleted.append(key_deleted)
                    l_replaced.append(key_replaced)
                    l_coupled.append(key_deleted + key_replaced)

    return l_deleted, l_replaced, l_coupled, l_inversion, n_unnecessary

if __name__ == """__main__""":

    df_text = pd.read_csv("../selfspy_df.csv")

    l_deleted, l_replaced, l_coupled, l_inversion= [], [], [], []
    n_unnecessary, n_inversion = 0, 0

    for s in df_text["text"]:
        l_deleted_new, l_replaced_new, l_coupled_new, l_inversion_new, n_unnecessary_new = keys_around_backspace(s)
        l_deleted.extend(l_deleted_new)
        l_replaced.extend(l_replaced_new)
        l_coupled.extend(l_coupled_new)
        l_inversion.extend(l_inversion_new)
        n_unnecessary += n_unnecessary_new


    print("{} unnecessary backspace".format(n_unnecessary))
    print("{} inverted letters (ts instead of st)".format(len(l_inversion)))
    print("{} deleted letters (excluding unnecessary backspace and inversions)".format(len(l_deleted)))
    print
    print("most missed keys (excluding inversions): ")
    print(sorted_unique(l_replaced))
    print
    print("the keys you most type instead of another (excluding inversions): ")
    print(sorted_unique(l_coupled))
    print
    print("the keys you most invert (ts instead of st): ")
    print(sorted_unique(l_inversion))
