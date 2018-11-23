#!/usr/bin/python3  
# coding: utf-8

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import datetime
import os

import myBigQuery


# WEBから情報取得してJSONを返す
def getJamJSON():
    # URL
    urlRoot = "http://c-nexco.highway-telephone.jp/main/index.php?"

    # top page取得
    r = requests.get(urlRoot)
    soupRoot = BeautifulSoup(r.content, "html.parser")
    print(soupRoot.title.string)

    #道路毎ページへのリンク取得
    jamInfo = {}
    roadlinks = [a for a in soupRoot.find_all("a",href=re.compile("infoselect.php[?]road="))]
    for road in roadlinks:
        #道路毎ページ取得
        roadName = road.getText()
        print(roadName)
        jamInfo[roadName] = {}
        url = urllib.parse.urljoin(urlRoot, road['href'])
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        #渋滞地点別情報ページへのリンク取得
        jamInfo[roadName]['jam'] = {}
        jamInfo[roadName]['jam']['url'] = url
        jamInfo[roadName]['jam']['pts'] = []
        jamlinks = [a for a in soup.find_all("a",href=re.compile("jamdetail.php[?]road="))]
        for j in jamlinks:
          #渋滞地点毎情報ページの読み込み
          jamId = j['href']
          u = urllib.parse.urljoin(url, j['href'])
          #print(u)
          r = requests.get(u)
          #print(r.encoding)
          #print(type(r.text))
          #print(type(r.content))
          html = r.text
          jamPt = { 'jamId' : jamId, 'href' : u, 'html' : html, 'info' : {} }
          s = BeautifulSoup(r.content, "html.parser")
          #テーブル列取得
          tbl = s.select("div.nexcosp-traffic-information table tr")
          for row in tbl:
            r = BeautifulSoup(str(row), "html.parser")
            th = r.th.text.strip()
            if th == "先頭位置":
              th = "loc"
            elif th == "渋滞原因":
              th = "cause"
            elif th == "渋滞長":
              th = "length"
            elif th == "渋滞通過時間":
              th = "tat"
            td = "".join(map(str, r.td.contents))
            #td = "".join(r.td.text)
            jamPt['info'][th] = td
            record = [roadName, jamId, th, td]#, html]
            #print(record)

          jamInfo[roadName]['jam']['pts'].append(jamPt)


    #import pprint
    #pprint.pprint(jamInfo)

    #JSONに変換
    import json
    #d = json.dumps(jamInfo, ensure_ascii=False, indent=4)
    d = json.dumps(jamInfo, ensure_ascii=False)

    #with open("out.json","w") as f:
    #  json.dump(jamInfo, f, ensure_ascii=False, indent=4)

    return d


def send():
    #try:
    # JSON取得
    json = getJamJSON()
    # 日付取得
    JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
    dt = datetime.datetime.now(JST)
    timestr = dt.strftime("%Y-%m-%d %H:%M:%S JST")
    # 送信
    myBigQuery.triggerBigQuery("jam_rcv", [[timestr, json, "", ""]])
    #except:
    #import traceback
    #traceback.print_exc()

if __name__ == '__main__':
    send()


