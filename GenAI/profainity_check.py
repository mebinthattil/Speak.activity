# Copyright (C) 2025, Mebin J Thattil <mail@mebin.in>

import base64
import os

def encode(string):
    return base64.b64encode(string.encode('utf-8'))
    
def decode(string):
    return base64.b64decode(string.encode('utf-8'))

def bad_word_list() -> list:
    with open(os.path.join(os.path.dirname(__file__), "profainity_blacklist.txt"), "r") as f: #the main reason why we have it encoded in b64 is so that even if a kid stumbles across this txt file by mistake they wont be able to understand anything
        a = f.readlines()
    decoded_list = [base64.b64decode(line.strip()).decode('utf-8') for line in a]

    return decoded_list