import re
import io
import os
import datetime
import pprint
import chardet
#import math

import myBigQuery

#from memory_profiler import profile
#@profile
#def test():
#  return 1
#test()

def tofloat(s):
  return float(str(s).replace(",",""))

def datefmt(s):
  a = s.replace("/","-").strip().split("-")
  if len(a) == 3:
    return "%s/%02d/%02d" % (a[0], int(a[1]), int(a[2]))
  else:
    return "%s/%02d/00" % (a[0], int(a[1]))

# get All _KakeiboData from BiigQuery and make dict 
def getHistDic():
  sql = """
      WITH
      A as (
        SELECT himoku, utiwake, REGEXP_REPLACE(biko,'[0-9]','') as biko, mark, account
        FROM `proven-mystery-220011.HOME_IoT.kakeibo_data_newest`
        where biko is not NULL AND account is not NULL AND account != '現金'
      ),
      B as (
        SELECT himoku, utiwake, biko, mark, 
          count(*) as cnt,  
          ROW_NUMBER() OVER (PARTITION BY biko ORDER BY count(*) desc) as num
        FROM A
        where biko is not NULL AND account is not NULL AND account != '現金'
        group by himoku, utiwake, biko, mark
      )
      select himoku, utiwake, biko, mark from B where num = 1
    """
  df = myBigQuery.queryBigQuery(sql)
  dic = {}
  for i, row in df.iterrows():
    dic[row["biko"]] = {"himoku":row["himoku"], 
                        "utiwake":row["utiwake"], 
                        "mark":row["mark"] if row["mark"] else ""}
  return dic

# read CSV and retern list of lists
def getDataCsv(csvfile, start=datetime.datetime(1900,1,1), end=datetime.datetime(2999,12,31)):
  import pandas as pd  # require about 60MB memory

  dic = getHistDic()

  accountName = {"楽天銀行":"イーバンク",
                 "十六銀行":"十六銀行",
                 "三菱UFJ銀行":"MUFG銀行",
                 "三井住友銀行":"さくら総合",
                 "ゆうちょ銀行":"郵便貯金普通"}

  ptn_rakuten = r"利用日,利用店名・商品名,利用者,支払方法,利用金額,支払手数料,支払総額"
  ptn_bankmeisai = r"取引日,名義,会社名,出金,入金,残高,摘要,備考,取引先支店名"
  ptn_bank = r"会社名,支店,口座種別,口座番号,残高"
  ptn_jwest = r"ご利用者,カテゴリ,ご利用日,ご利用先など,ご利用金額\(￥\),支払区分,今回回数,訂正サイン,お支払い金額\(￥\),国内／海外"

  # read csv file
  with open(csvfile, "rb") as f:
    enc = chardet.detect(f.read())["encoding"]
  with open(csvfile, "r", encoding=enc) as f:
    lines = f.readlines()
  print("".join(lines).replace('"',''))
  print("read csv %d lines" % len(lines))
  # detect csv type
  if re.search(ptn_rakuten, "".join(lines).replace('"','')):
    print("RAKUTEN CARD")
    ptn = ptn_rakuten
  elif re.search(ptn_bankmeisai, "".join(lines).replace('"','')):
    print("BANK MEISAI (moneyLook)")
    ptn = ptn_bankmeisai
  elif re.search(ptn_bank, "".join(lines).replace('"','')):
    print("BANK (moneyLook)")
    ptn = ptn_bank
  elif re.search(ptn_jwest, "".join(lines).replace('"','')):
    print("JWEST CARD")
    ptn = ptn_jwest
  else:
    print("error: csv header no match")
    exit(1)

  # skip before header line, and read CSV
  with io.StringIO("") as sio:
    flag = False
    for l in lines:
      if re.match(ptn, l.replace('"','')):
        flag = True
      if flag == True:
        sio.write(l)
    sio.seek(0)
    df = pd.read_csv(sio)
  #print(df)

  mat = []
  if ptn == ptn_rakuten:
    for index, row in df.iterrows():
      #print(row)
      date = datefmt(row["利用日"])
      biko = row["利用店名・商品名"]
      himoku = dic[biko]["himoku"] if biko in dic else ""
      utiwake = dic[biko]["utiwake"] if biko in dic else ""
      income = 0
      outgo = row["支払総額"]
      mark = dic[biko]["mark"] if biko in dic else ""
      account = "楽天カード"
      mat.append(["","",date, himoku, utiwake, biko, mark, income, outgo, "", account])
  elif ptn == ptn_bankmeisai:
    for index, row in df.iterrows():
      date = datefmt(row["取引日"])
      biko = str(row["摘要"]) + str(row["備考"]).replace("nan","")
      b = re.sub(r"[0-9]","",biko)
      himoku = dic[b]["himoku"] if biko in dic else ""
      utiwake = dic[b]["utiwake"] if biko in dic else ""
      income = row["入金"]
      outgo = row["出金"]
      mark = dic[b]["mark"] if biko in dic else ""
      account = accountName[row["会社名"]]
      mat.append(["","",date, himoku, utiwake, biko, mark, income, outgo, "", account])
  elif ptn == ptn_bank:
    for index, row in df.iterrows():
      date = re.sub(r"[^_]*_(\d\d\d\d)(\d\d)(\d\d).csv","\\1/\\2/\\3",csvfile)
      biko = row["残高"]
      himoku = "使途不明金"
      utiwake = "残高合せ込み"
      income = 0
      outgo = 0
      mark = ""
      account = accountName[row["会社名"]]
      mat.append(["","",date, himoku, utiwake, biko, mark, income, outgo, "", account])
  elif ptn == ptn_jwest:
    for index, row in df.iterrows():
      date = datefmt(row["ご利用日"])
      biko = row["ご利用先など"]
      b = re.sub(r"[0-9]","",biko)
      himoku = dic[b]["himoku"] if biko in dic else ""
      utiwake = dic[b]["utiwake"] if biko in dic else ""
      income = 0
      outgo = tofloat(row["お支払い金額(￥)"])
      if str(outgo) == "nan":
        continue
      mark = dic[b]["mark"] if biko in dic else ""
      account = "JWEST"
      mat.append(["","",date, himoku, utiwake, biko, mark, income, outgo, "", account])

  # filter by start, end dates
  #pprint.pprint(mat, width=200,depth=2)
  s_start = start.strftime("%Y/%m/%d")
  s_end = end.strftime("%Y/%m/%d")
  mat = [m for m in mat if m[2] >= s_start and m[2] <= s_end]
  return mat

# read HTML file/text 
def getDataHtml(html):
  from bs4 import BeautifulSoup

  dic = getHistDic()

  if os.path.exists(html):
    with open(html, "rb") as f:
      enc = chardet.detect(f.read())["encoding"]
    with open(html, "r", encoding=enc) as f:
      html_str = f.read()
  else:
    html_str = html

  soup = BeautifulSoup(html_str, "html.parser")
  div = soup.findAll("div",{"class":"mic-block-scroll-table__inner"})[0]
  table = div.findAll("table")[0]
  rows = table.findAll("tr")
  mat = []
  for row in rows:
      csvRow = []
      for cell in row.findAll(['td', 'th']):
          csvRow.append(cell.get_text())
      print(csvRow)
      if len(csvRow) == 6:
        date = datefmt(csvRow[0])
        biko = csvRow[1]
        b = re.sub(r"[0-9]","",biko)
        himoku = dic[b]["himoku"] if biko in dic else ""
        utiwake = dic[b]["utiwake"] if biko in dic else ""
        mark = dic[b]["mark"] if biko in dic else ""
        income = 0
        outgo = tofloat(csvRow[5].replace("円","").replace(",","").strip())
        account = "MICARD"
        mat.append(["","",date, himoku, utiwake, biko, mark, income, outgo, "", account])
  print("read %d rows" % len(rows))
  return mat

if __name__ == "__main__":
  import sys
  file = sys.argv[1]
  if re.search(r".(csv|CSV)$",file):
    values = getDataCsv(file)
  else:
    values = getDataHtml(file)
  pprint.pprint(values, width=200, depth=2)
  print("sending %d records" % len(values))
  import myGSpread
  myGSpread.appendRows(values, "家計簿", "検索")
  input("enter any key to exit")

