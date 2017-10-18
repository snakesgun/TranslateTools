import urllib
import requests
import json
import re
import random
import sys
import time
import os

HEADERS = {
    "connection": "keep-alive",
    "Accept": "text/html, application/xhtml+xml, */*",
    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko"
    }


class BaiduTransEngine(object):

    def __init__(self):
        self.headers = HEADERS
        self.retry_times = 0

    def baidu_trans(self, termStr, src='en', dst='zh'):
        """
        baidu_trans(termStr, src='en', dst='zh')
Translate termStr (a str) by using baidu fanyi translate engine, and return a python dictionary object.

src, source language of termStr. By default this is equivalent to 'en'. If source language has been changed to another language, we shoud use this parameter ostensively.

dst, destination language of termStr. By default this is equivalent to 'zh'. If destination language has been changed to another language, we shoud use this parameter ostensively.
        """
        url = self.__url_generator(termStr, src=src, dst=dst)
        while True:
            try:
                engine_response = self.__translate(url)
                trans_result = self.__response_parser(engine_response, termStr, src)
                # print(termStr + " Succeed")
                self.retry_times = 0
                return trans_result
                break
            except Exception as e:
                sleep_time = random.randint(5, 15)
                print(e.__str__() + "Translate failed, re-try")
                self.retry_times += 1
                print(self.retry_times)
                if self.retry_times >= 20:
                    time.sleep(120)
                else:
                    time.sleep(sleep_time)
                continue

    def __url_generator(self, termStr, src, dst):
        quoteStr = urllib.parse.quote(termStr)
        url = "http://fanyi.baidu.com/v2transapi?from={sr}&to={tg}&query={qt}&transtype=translang&simple_means_flag=3".format(sr=src, tg=dst, qt=quoteStr)
        return url

    def __translate(self, url):
        r = requests.get(url, headers=self.headers, timeout=60)
        response = json.loads(r.text)
        return response

    def __response_parser(self, res, termStr, src):
        total_res = {"term": termStr}
        # Get API result from translation engine response
        total_res["trans"] = self.__trans_parser(res)
        # Get sentences result from translation engine response
        # If we get sentences result
        if res["liju_result"]:
            if res["liju_result"]["double"]:
                total_res["sents"] = self.__sents_parser(res, termStr, src)
                # total_res["sents"] = sorted(total_res["sents"], key=lambda x: len(x.split("，")))
            else:
                total_res["sents"] = ["null"]
        # If we do not get sentences result
        else:
            total_res["sents"] = ["null"]
        if res["dict_result"]:
            total_res["dicts"] = self.__dicts_parser(res)
        else:
            total_res["dicts"] = ["null"]
        return total_res

    def __trans_parser(self, res):
        trans_res = res["trans_result"]["data"][0]["dst"]
        return trans_res

    def __sents_parser(self, res, termStr, src):
        reflect_dict = {}
        en_ele = {}
        cn_ele = {}
        term = termStr
        # get reflection between word and postion
        for sent in json.loads(res["liju_result"]["double"], encoding="utf-8"):
            hl_en = []
            hl_cn = []
            for en in sent[0]:
                en_ele[en[1]] = en[0]
                if en[3] == 1:
                    hl_en.append(en[2])
                else:
                    pass
            for cn in sent[1]:
                cn_ele[cn[1]] = cn[0]
                if cn[3] == 1:
                    hl_cn.append(cn[2])
                else:
                    pass
        # get reflcetion result
            tmp_en = []
            tmp_cn = []
            for cn_en in sorted(list(set(hl_en)), key=lambda x: int(x.split(",")[0][2:])):
                positons = cn_en.split(",")
                for i in positons:
                    if i in en_ele.keys():
                        tmp_en.append(int(i[2:]))
                    else:
                        tmp_cn.append(int(i[2:]))
            # If there is some commas in term, it is no necessary to determine whether reflected words are continuously
            if ", " in term or "，" in term:
                tmp_en = ["w_" + str(i) for i in tmp_en]
                tmp_cn = ["w_" + str(i) for i in tmp_cn]
                if src == 'zh':
                    reflect_en = "".join(tmp_en)
                    if len(re.split(",|，", term)) > 2:
                        reflect_cn = cn_ele[tmp_cn[0]] + ", " + ", ".join([cn_ele[i] for i in tmp_cn[1:]])
                    else:
                        reflect_cn = cn_ele[tmp_cn[0]] + ", " + " ".join([cn_ele[i] for i in tmp_cn[1:]])
                else:
                    reflect_en = " ".join(tmp_en)
                    if len(re.split(",|，", term)) > 2:
                        reflect_cn = cn_ele[tmp_cn[0]] + "，" + "，".join([cn_ele[i] for i in tmp_cn[1:]])
                    else:
                        reflect_cn = cn_ele[tmp_cn[0]] + "，" + "".join([cn_ele[i] for i in tmp_cn[1:]])
                if reflect_cn in reflect_dict.keys():
                    reflect_dict[reflect_cn] += 1
                else:
                    reflect_dict[reflect_cn] = 1
            else:
                tmp_cn.sort()
                tmp_en.sort()
                # To determine whether reflected word are continuously
                if tmp_en[-1] - tmp_en[0] == len(tmp_en) - 1:
                    tmp_en = ["w_" + str(i) for i in tmp_en]
                    tmp_cn = ["w_" + str(i) for i in tmp_cn]
                    if src == 'zh':
                        reflect_en = "".join([en_ele[i] for i in tmp_en])
                        reflect_cn = " ".join([cn_ele[i] for i in tmp_cn])
                    else:
                        reflect_en = " ".join([en_ele[i] for i in tmp_en])
                        reflect_cn = "".join([cn_ele[i] for i in tmp_cn])
                    if reflect_cn in reflect_dict.keys():
                        reflect_dict[reflect_cn] += 1
                    else:
                        reflect_dict[reflect_cn] = 1
                else:
                    continue
        if reflect_dict:
            return [i[0]for i in sorted(reflect_dict.items(), key=lambda d: d[1], reverse=True)[:2]]
        else:
            return ["null"]

    def __dicts_parser(self, res):
        dict_res = []
        try:
            if "netdata" in res["dict_result"]:
                if "word_means" in res["dict_result"]["simple_means"]:
                    dict_means = list(res["dict_result"]["simple_means"]["word_means"])
                elif "means" in res["dict_result"]["simple_means"]["symbols"][0]["parts"][0]:
                    dict_means = list(res["dict_result"]["simple_means"]["symbols"][0]["parts"][0]["means"])
                else:
                    dict_means = [res["dict_result"]["netdata"]["types"][0]["trans"]]
            else:
                if "word_means" in res["dict_result"]["simple_means"]:
                    dict_means = list(res["dict_result"]["simple_means"]["word_means"])
                elif "has_mean" in res["dict_result"]["simple_means"]["symbols"][0]["parts"][0]["means"][0]:
                    dict_means = [i["word_mean"] for i in res["dict_result"]["simple_means"]["symbols"][0]["parts"][0]["means"]]
                elif "means" in res["dict_result"]["simple_means"]["symbols"][0]["parts"][0]:
                    dict_means = list(res["dict_result"]["simple_means"]["symbols"][0]["parts"][0]["means"])
        except KeyError as e:
            dict_means = ["null"]
        dict_res = dict_means
        return dict_res

bt = BaiduTransEngine()
baidu_trans = bt.baidu_trans


def main():
    print(baidu_trans("肺癌", src='zh', dst='en'))

if __name__ == '__main__':
    main()
