import re
import io
import datetime
import pprint

import myBigQuery

#from memory_profiler import profile
#@profile
#def test():
#  return 1
#test()

def tofloat(s):
  return float(str(s).replace(",",""))

def datefmt(s):
  a = s.replace("/","-").split("-")
  return "%s-%02d-%02d" % (a[0], int(a[1]), int(a[2]))

# read CSV and retern list of lists
def getDataCsv(csvfile, start, end):
  import pandas as pd  # require about 60MB memory

  sql = """
      WITH
      D as (
        SELECT himoku, utiwake, biko, mark, 
          count(*) as cnt,  
          ROW_NUMBER() OVER (PARTITION BY biko ORDER BY count(*) desc) as num
        FROM `proven-mystery-220011.HOME_IoT.kakeibo_data_newest`
        where biko is not NULL AND account is not NULL AND account != '現金'
        group by himoku, utiwake, biko, mark
      )
      select himoku, utiwake, biko, mark from D where num = 1
    """
  df = myBigQuery.queryBigQuery(sql)
  dic = {}
  for i, row in df.iterrows():
    dic[row["biko"]] = {"himoku":row["himoku"], 
                        "utiwake":row["utiwake"], 
                        "mark":row["mark"] if row["mark"] else ""}

  ptn_rakuten = r"利用日,利用店名・商品名,利用者,支払方法,利用金額,支払手数料,支払総額"
  ptn_bankmeisai = r"取引日,名義,会社名,出金,入金,残高,摘要,備考,取引先支店名"
  ptn_bank = r"会社名,支店,口座種別,口座番号,残高"

  # read csv file
  with open(csvfile, "r", encoding="shift_jis") as f:
    lines = f.readlines()
  #print("".join(lines).replace('"',''))
  # check csv type
  if re.search(ptn_rakuten, "".join(lines).replace('"','')):
    print("RAKUTEN CARD")
    ptn = ptn_rakuten
  elif re.search(ptn_bankmeisai, "".join(lines).replace('"','')):
    print("BANK MEISAI (moneyLook)")
    ptn = ptn_bankmeisai
  elif re.search(ptn_bank, "".join(lines).replace('"','')):
    print("BANK (moneyLook)")
    ptn = ptn_bank
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

  mat = []
  if ptn == ptn_rakuten:
    for index, row in df.iterrows():
      #print(row)
      date = datefmt(row["利用日"])
      biko = row["利用店名・商品名"]
      himoku = dic[biko]["himoku"] if biko in dic else ""
      utiwake = dic[biko]["utiwake"] if biko in dic else ""
      income = 0 #row["支払総額"]
      outgo = row["支払総額"]
      mark = dic[biko]["mark"] if biko in dic else ""
      account = "楽天カード"
      mat.append(["","",date, himoku, utiwake, biko, mark, income, outgo, "", account])
  elif ptn == ptn_adsbi:
    for index, row in df.iterrows():
      #print(row)
      date = datefmt(row["入出金日"])
      t = row["摘要"]
      if not re.search(r"配当金",t):
        continue
      name = re.sub(r"^.*配当金\s+(.*)$","\\1", t)
      account = "ETRADE"
      if row["区分"] == "入金":
        paid = tofloat(row["入金額"]) * -1
      elif row["区分"] == "出金":
        paid = tofloat(row["出金額"])
      amount = 0
      price = 0
      comment = row["摘要"]
      mat.append([date, name, account, paid, amount, price, comment])

  # filter by start, end dates
  #pprint.pprint(mat, width=200,depth=2)
  s_start = start.strftime("%Y-%m-%d")
  s_end = end.strftime("%Y-%m-%d")
  mat = [m for m in mat if m[2] >= s_start and m[2] <= s_end]
  return mat

if __name__ == "__main__":
  import sys
  file = sys.argv[1]
  start = datetime.datetime(1970,1,1)
  end = datetime.datetime.today() - datetime.timedelta(days=2)
  values = getDataCsv(file, start, end)
  pprint.pprint(values, width=200, depth=2)
  import myGSpread
  myGSpread.insertRows(values, "家計簿", "検索", 0)
  input("enter any key to exit")

