import re
import pandas as pd
import numpy as np


# TODO:
# 1) Normalize missing rate of pairs of keys by frequency
# 2) Take uncertainty into account when displayin worst keys
# 3) Add tests
# 4) take into account clicks (probably hard)
# 5) check if there is an error anywhere in the deleted text (right now we only look at the last letter)
# check distance betweeen the deleted word and the replaced word : if it's too big doesn't count. And look at all the diff
# Related : take into account the case where spirt<[Backspace]x5>port (count as an unnecessary backspace now, but there aren't too many)
# 6) I've just noticed in selfstats row.decrypt_keys() instead of row.decrypt_text(), which gives directly a list of keys pressed.
# Are we sure regex are still the best solution with this function ??


#############
# Brief explanation (to expand):

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

def sorted_unique_rates(array, n, dic_counts):
    """
    like sorted unique but sort by the rate (count in the array / base count) thanks to a dictionnary providing the base count
    :param array: array to analyse
    :param n: number of results
    :param dic_freq: dictionnary containing the base count of the elements of the array
    :return: top n letters, top n rates
    """
    n = min(n, len(array))
    ar, count = np.unique(array, return_counts=True)
    rates = np.array([float(count[i]) / dic_counts[ar[i]] for i in range(len(count))]) # TODO the condition should'nt be necessaary
    indices = np.argsort(-rates)
    uncertainty = [1.96 * np.sqrt(rates[i] * (1 - rates[i]) / float(count[i])) for i in indices] # binomial uncertainty
    return ar[indices][:n], rates[indices][:n], uncertainty[:n]

def find_keys_typed_instead(key, l_coupled, n=10):
    couples, counts = np.unique(l_coupled, return_counts=True)
    matched_indices = [i for i in range(len(couples)) if len(couples[i]) > 1 and couples[i][1]==key]
    matched_couples, matched_counts = couples[matched_indices], counts[matched_indices]
    total_counts = sum(matched_counts)
    sorted_indices = np.argsort(-matched_counts)
    sorted_couples = matched_couples[sorted_indices]
    sorted_rates = [float(count) / total_counts for count in matched_counts[sorted_indices]]
    return [couple[0] for couple in sorted_couples[:n]], sorted_rates[:n]


def sorted_unique_rates_coupled(array, n, dic_counts):
    """

    :param array: array of string char1char2 where char1 has been typed instead of char2
    :param n: number of results to display
    :param dic_counts: frequency of characters in the whole db
    :return: top n couples, top n rates
    """
    n = min(n, len(array))
    ar, count = np.unique(array, return_counts=True)

    rates = np.array([float(count[i]) / dic_counts[ar[i][1]] for i in range(len(count)) if len(ar[i]) > 1]) # TODO the conditions should'nt be necessaary
    indices = [i for i in np.argsort(-rates) if len(ar[i]) > 1] # TODO the condition should'nt be necessaary
    return ar[indices][:n], rates[indices][:n]


def display_typing_quality(dic, n=15):
    """
    Display typing quality statistics for selfstats
    :param dic: dic of the form {l_deleted, l_correct, l_coupled, l_inversion, n_unnecessary}
    :return: None
    """
    print("{} unnecessary backspace".format(dic["n_unnecessary"]))
    print("{} inverted letters (e.g ts instead of st)".format(len(dic["l_inversion"])))
    print("{} deleted letters (excluding unnecessary backspace and inversions)".format(len(dic["l_deleted"])))
    print
    print("Most missed keys (excluding inversions): ")


    # show ratio of missed / typed
    keys, rates, uncertainty = sorted_unique_rates(dic["l_correct"], n, dic["dic_char_count"])
    for i, key in enumerate(keys):
        print(u"Key: {} ({}% missed +- {}%)".format(key, int(rates[i] * 100), int(uncertainty[i] * 100)))
        keys_instead, rates_instead = find_keys_typed_instead(key, dic["l_coupled"], 5)

        print(u"Typed instead: {}".format(", ".join([keys_instead[i] + " (" + str(int(rates_instead[i] * 100)) + "%)" for i in range(len(keys_instead))])))
       # for j in range(len(keys_instead)):
        #    print(keys_instead[j][0])
        #    print(u"{} instead ({}%)".format(keys_instead[j][0], int(rates_instead[j]*100)))
    print

    speeds_keys = np.array([np.mean(dic["dic_key_speed"][key]) for key in dic["dic_key_speed"].keys()])
    std_speeds_keys = np.array([np.std(dic["dic_key_speed"][key]) for key in dic["dic_key_speed"].keys()])
    keys = [key for key in dic["dic_key_speed"].keys()]
    indices_keys = np.argsort(-speeds_keys)
    print("Keys typed most slowly:")
    for i in indices_keys[:n]:
        print(u"Key: {}  ({} seconds +- {})".format(keys[i], speeds_keys[i], 2 * std_speeds_keys[i])) #gaussian approx of 95 interval
    print

    speeds_cmd = np.array([np.mean(dic["dic_cmd_speed"][key]) for key in dic["dic_cmd_speed"].keys()])
    std_speeds_cmd = np.array([np.std(dic["dic_cmd_speed"][key]) for key in dic["dic_cmd_speed"].keys()])
    cmds = [cmd for cmd in dic["dic_cmd_speed"].keys()]
    indices_cmd = np.argsort(-speeds_cmd)
    print("Commands typed most slowly: (less trustable)")
    for i in indices_cmd[:n]:
        print(u"Command: {} ({} seconds +- {})".format(cmds[i], speeds_cmd[i], 2 * std_speeds_cmd[i])) #gaussian approx of 95 interval




    ############
    # Probably not so useful to display
    ##########
    #print("Keys you most type instead of another (excluding inversions): ")
    #keys_couple, rates_couple = sorted_unique_rates_coupled(dic["l_coupled"], len(dic["l_coupled"]), dic["dic_char_count"])
    #for i in range(n):
    #    print(u"Keys : {} instead of {} ({}%)".format(keys_couple[i][0], keys_couple[i][1], int(rates_couple[i] * 100)))
    #print

    # print("Keys you most invert (e.g ts instead of st): ")
    # keys, counts = sorted_unique(dic["l_inversion"], n)
    # for i in range(len(keys)):
    #     print(u"Keys: {} instead of {} ({} times)".format(keys[i][0] + keys[i][1], keys[i][1] + keys[i][0], counts[i]))


def create_dic():
    """
    Create the dictionnary which stores the results of key_around_backspace. Useful to make change easier while leaving
     selfstats code intact.
    :return: the created dictionnary
    """
    dic = {"l_deleted": [], "l_correct": [], "l_coupled": [], "l_inversion": [], "n_unnecessary": 0, "dic_char_count": {}, "dic_key_speed": {}, "dic_cmd_speed": {}}

    return dic


def update_dic(dic, text, keys, times):
    """
    :param dic:  dic of the form {l_deleted, l_correct, l_coupled, l_inversion, n_unnecessary}
    :param text: new text to analysie
    :param keys: list of keys (corresponding to text)
    :param times: list of times (corresponding to keys
    :return: the updated dictionnary
    """
    dic = count_keys(text, dic) # TODO : count_keys and keys_around_backspace don't have the same structure

    l_deleted_new, l_correct_new, l_coupled_new, l_inversion_new, n_unnecessary_new = keys_around_backspace(text)
    dic["l_deleted"].extend(l_deleted_new)
    dic["l_correct"].extend(l_correct_new)
    dic["l_coupled"].extend(l_coupled_new)
    dic["l_inversion"].extend(l_inversion_new)
    dic["n_unnecessary"] += n_unnecessary_new

    dic = key_speeds(keys, times, dic)

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
    #TODO test
    #TODO check there are no pb with < and >
    match_1_backspace = re.findall("([^\>])\<\[[^\]]*Backspace\]\>([^\<]+)(?:\<|\Z)", s) # match jfksdfj<[Backspace]>jdskjd and return the erased letter and the replacement text
    match_more_backpace = re.findall("(?:\A|\>)([^\>]+)\<\[[^\]]*Backspace\]x(\d*)\>([^\<]+)(?:\<|\Z)", s)# match dfdfkl<[Backspace]x2>kjkfkdjf etc. and return the erased letter and the replacement text
    l_deleted, l_correct, l_coupled, l_inversion = [], [], [], []
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
                if len(key_replaced) >= 1:
                    l_correct.append(key_replaced)
                    if len(key_deleted) >= 1:
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
                    if len(key_replaced) >= 1:
                        l_correct.append(key_replaced)
                        if len(key_deleted) >= 1:
                            l_coupled.append(key_deleted + key_replaced)

    return l_deleted, l_correct, l_coupled, l_inversion, n_unnecessary

def count_keys(s, dic):
    #TODO : test
    #TODO : isn't it simpler is we use row.decrypt_keys instead of row.decrypt_text ?
    match = re.findall("(?:\A|\>)(.+?)(?:\<\[|\Z)", s)
    for group in match:
        keys, counts = np.unique(list(group), return_counts=True)
        for i, key in enumerate(keys):
            if key not in dic["dic_char_count"].keys():
                dic["dic_char_count"][key] = counts[i]
            else:
                dic["dic_char_count"][key] += counts[i]

    return dic

def key_speeds(keys, times, dic):
    #TODO test
    #TODO what about <[Backspace]x2>
    #TODO : what about repeated char (when I leave my finger on the keys)
    #TODO : combine speed with correctness (if you want to type g but you type f<[Backspace]>g you should count the time to type the three keys for g)
    for i, key in enumerate(keys):
        if (i > 1 and keys[i-1][:2] != "<["): #we don't count the time when the key is typed after a command (cause there is probably reflexion involved)
            if key[:2] == "<[": #if it's a command:
                if key not in dic["dic_cmd_speed"].keys():
                    dic["dic_cmd_speed"][key] = [times[i]]
                else:
                    dic["dic_cmd_speed"][key].append(times[i])
            else:
                if key not in dic["dic_key_speed"].keys():
                    dic["dic_key_speed"][key] = [times[i]]
                else:
                    dic["dic_key_speed"][key].append(times[i])
    return dic




if __name__ == """__main__""":

    df_text = pd.read_csv("../selfspy_df.csv")

    l_deleted, l_correct, l_coupled, l_inversion= [], [], [], []
    n_unnecessary, n_inversion = 0, 0

    for s in df_text["text"]:
        l_deleted_new, l_correct_new, l_coupled_new, l_inversion_new, n_unnecessary_new = keys_around_backspace(s)
        l_deleted.extend(l_deleted_new)
        l_correct.extend(l_correct_new)
        l_coupled.extend(l_coupled_new)
        l_inversion.extend(l_inversion_new)
        n_unnecessary += n_unnecessary_new


    print("{} unnecessary backspace".format(n_unnecessary))
    print("{} inverted letters (ts instead of st)".format(len(l_inversion)))
    print("{} deleted letters (excluding unnecessary backspace and inversions)".format(len(l_deleted)))
    print
    print("most missed keys (excluding inversions): ")
    print(sorted_unique(l_correct))
    print
    print("the keys you most type instead of another (excluding inversions): ")
    print(sorted_unique(l_coupled))
    print
    print("the keys you most invert (ts instead of st): ")
    print(sorted_unique(l_inversion))
