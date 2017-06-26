import requests
import json
import re
import sys
import time
import ctypes
import os
import multiprocessing


def get_tkk():
    """
    Get TKK from the Internet, pull a request to google translate for next step everytime
    """
    r = requests.get("https://translate.google.cn")
    # print(r.encoding)
    tkk_str = r.content.decode("gbk")
    # print(tkk_str)
    target_num = re.compile(r"TKK=eval\('\(\(function\(\)\{var\s+a\\x3d(-*\d+);var\s+b\\x3d(-*\d+);return\s+(\d+)\+")
    targets = target_num.search(tkk_str).groups()
    # print(targets)
    tkk = targets[2] + "." + str(int(targets[0]) + int(targets[1]))
    # print(tkk)
    return tkk


def tk(a):
    tkk = get_tkk()
    # tkk = "411728.3522083429"
    e = tkk.split(".")
    h = int(e[0]) or 0
    g = []
    d = 0
    for f in range(len(a)):
        c = ord(a[f])
        if c < 128:
            g.insert(d, c)
            d += 1
        else:
            if c < 2048:
                g.insert(d, ctypes.c_int32(c >> 6 | 192).value)
                d += 1
            else:
                if (55296 == ctypes.c_int32(c & 64512).value) and ((f + 1) < len(a)) and (56320 == ord(a[f + 1])):
                    f += 1
                    c = ctypes.c_int32(65536 + ((c & 1023) << 10)).value + ctypes.c_int32((ord(a[f]) & 1023)).value
                    g.insert(d, ctypes.c_int32(c >> 18 | 240).value)
                    d += 1
                    g.insert(d, ctypes.c_int32(c >> 12 & 63 | 128).value)
                    d += 1
                else:
                    g.insert(d, ctypes.c_int32(c >> 12 | 224).value)
                    d += 1
                    g.insert(d, ctypes.c_int32(c >> 6 & 63 | 128).value)
                    d += 1
                g.insert(d, ctypes.c_int32(c & 63 | 128).value)
                d += 1
    a = h
    for d in range(len(g)):
        a += g[d]
        a = b(a, "+-a^+6")
    # print(a, 1)
    a = b(a, "+-3^+b+-f")
    # print(a, 2)
    a = ctypes.c_int(a ^ (int(e[1]) or 0)).value
    if a >= 0:
        pass
    else:
        a = ctypes.c_int32((a & 2147483647)).value + 2147483648
    a %= int(1E6)
    # print(a, 3)
    return str(a) + "." + str(a ^ h)


def b(a, b):
    for d in range(0, len(b) - 2, 3):
        c = b[d + 2]
        if c >= "a":
            c = ord(c[0]) - 87
        else:
            c = int(c)
        if b[d + 1] == "+":
            c = rshiftNS(a, c)
        else:
            c = ctypes.c_int32(a << c).value
        if b[d] == "+":
            a = ctypes.c_int32(a + c & 4294967295).value
        else:
            a = ctypes.c_int32(a ^ c).value
    return a


def rshiftNS(val, n):
    """
    Bitwise operation of right shift with nosign
    - val : original value
    - n   : number of bit to shift
    """
    return val >> n if val >= 0 else (val + 0x100000000) >> n


def translate(query):
    url = "https://translate.google.cn/translate_a/t?client=webapp&sl=auto&tl=zh-CN&hl=en&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&source=bh&ssel=0&tsel=0&kc=1&tk=%s&q=%s" % (str(tk(query)), query)
    result_t = json.loads(requests.get(url).content.decode("utf8"))
    return result_t


if __name__ == "__main__":
    print(translate("dog"))
