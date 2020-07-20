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

def sorted_unique(array, n=10):
    """"sort the unique element of an array by count, and display the nth first"""
    n = min(n, len(array))
    ar, count = np.unique(array, return_counts=True)
    indices = np.argsort(-count)
    return ar[indices][:n], count[indices][:n]

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
    #TODO : improve it to check if there is an error anywhere in the deleted text (right now we only look at the last letter)
    # check distance betweeen the deleted word and the replaced word : if it's too big doesn't count. And look at all the diff

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
    print("{} inverted letters".format(len(l_inversion)))
    print("{} deleted letters (excluding unnecessary backspace and inversions)".format(len(l_deleted)))
    print("most deleted keys: ")
    print(sorted_unique(l_deleted))
    print("most replaced keys: ")
    print(sorted_unique(l_replaced))
    print("most coupled keys: ")
    print(sorted_unique(l_coupled))
    print("most inverted keys: ")
    print(sorted_unique(l_inversion))
