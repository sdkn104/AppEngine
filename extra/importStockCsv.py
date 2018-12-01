import re
import io
import datetime
import pprint

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
  ptn_sbi = r"約定日,銘柄,銘柄コード,市場,"
  ptn_adsbi = r"入出金日,区分,摘要,出金額,入金額,振替出金額,振替入金額"
  ptn_ch  = r"約定日,受渡日,銘柄コード,銘柄名,市場,"
  ptn_us  = r"約定日,受渡日,ティッカー,銘柄名,"
  ptn_adus = r"受渡日,約定日,口座区分,取引区分,対象証券名,決済通貨,単価,数量［株 /口］,受渡金額（受取）"
  ptn_adjp = r"受渡日,約定日,取引区分,口座区分,対象証券名,単価［円/％］,数量［株/口/額面］,受渡金額（受取）"
  # read csv file
  with open(csvfile, "r", encoding="shift_jis") as f:
    lines = f.readlines()
  #print("".join(lines).replace('"',''))
  # check csv type
  if re.search(ptn_sbi, "".join(lines).replace('"','')):
    print("SBI TRADE")
    ptn = ptn_sbi
  elif re.search(ptn_adsbi, "".join(lines).replace('"','')):
    print("SBI SHARE")
    ptn = ptn_adsbi
  elif re.search(ptn_ch, "".join(lines).replace('"','')):
    print("RAKUTEN CHINA TRADE")
    ptn = ptn_ch
  elif re.search(ptn_us, "".join(lines).replace('"','')):
    print("RAKUTEN US TRADE")
    ptn = ptn_us
  elif re.search(ptn_adus, "".join(lines).replace('"','')):
    print("RAKUTEN US SHARE")
    ptn = ptn_adus
  elif re.search(ptn_adjp, "".join(lines).replace('"','')):
    print("RAKUTEN JP SHARE")
    ptn = ptn_adjp
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
  if ptn == ptn_sbi:
    for index, row in df.iterrows():
      #print(row)
      date = datefmt(row["約定日"])
      name = row["銘柄"]
      account = "ETRADE"
      sign = 1 if row["取引"][-1] == "買" else (-1 if row["取引"][-1] == "売" else 0)
      amount = row["約定数量"] * sign
      price = row["約定単価"]
      paid =  amount * price - row["手数料/諸経費等"] - row["税額"]
      code = row["銘柄コード"]
      comment = code
      mat.append([date, name, account, paid, amount, price, comment])
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
  elif ptn == ptn_us:
    for index, row in df.iterrows():
      #print(row)
      date = datefmt(row["約定日"])
      name = row["銘柄名"]
      account = "楽天"
      sign = 1 if row["取引区分"][0] == "買" else (-1 if row["取引区分"][0] == "売" else 0)
      rate = tofloat(row["為替レート"])
      amount = tofloat(row["数量［株］"]) * sign
      price = tofloat(row["単価［USドル］"]) * rate
      paid = tofloat(row["受渡金額［USドル］"]) * sign * float(rate)
      code = row["ティッカー"]
      comment = "%s USDrate=%g" % (code, rate)
      mat.append([date, name, account, paid, amount, price, comment])
      name = "USDJPY"
      amount = tofloat(row["受渡金額［USドル］"]) * sign * -1
      price = rate
      paid = amount * rate
      comment = code
      mat.append([date, name, account, paid, amount, price, comment])
  elif ptn == ptn_ch:
    for index, row in df.iterrows():
      #print(row)
      date = datefmt(row["約定日"])
      name = row["銘柄名"]
      account = "楽天"
      sign = 1 if row["取引区分"][0] == "買" else (-1 if row["取引区分"][0] == "売" else 0)
      rate = tofloat(row["為替レート"])
      amount = tofloat(row["数量［株］"]) * sign
      price = tofloat(row["単価"]) * rate
      paid = tofloat(row["受渡金額［円］"]) * sign
      code = row["銘柄コード"]
      comment = "%s HKDrate=%g" % (code, rate)
      mat.append([date, name, account, paid, amount, price, comment])
  elif ptn == ptn_adjp:
    for index, row in df.iterrows():
      #print(row)
      print(row["取引区分"])
      if row["取引区分"] != "外株配当金":
        continue
      date = datefmt(row["約定日"])
      name = row["対象証券名"]
      account = "楽天"
      paid = tofloat(row["受渡金額（受取）"]) * -1
      amount = 0
      price = 0
      comment = "配当"
      mat.append([date, name, account, paid, amount, price, comment])
  elif ptn == ptn_adus:
    for index, row in df.iterrows():
      if row["取引区分"] != "外株配当金":
        continue
      date = datefmt(row["約定日"])
      name = row["対象証券名"] 
      account = "楽天"
      rate = tofloat(row["為替レート"])
      paid = tofloat(row["受渡金額（受取）"]) * rate * -1
      amount = 0
      price = 0
      comment = "配当 USDrate=%g" % (rate)
      mat.append([date, name, account, paid, amount, price, comment])
      comment = name
      name = "USDJPY"
      paid = paid * -1
      amount = paid / rate
      price = rate
      mat.append([date, name, account, paid, amount, price, comment])

  # filter by start, end dates
  #pprint.pprint(mat, width=200,depth=2)
  s_start = start.strftime("%Y-%m-%d")
  s_end = end.strftime("%Y-%m-%d")
  mat = [m for m in mat if m[0] >= s_start and m[0] <= s_end]
  return mat

if __name__ == "__main__":
  import sys
  file = sys.argv[1]
  start = datetime.datetime(1970,1,1)
  end = datetime.datetime.today() - datetime.timedelta(days=2)
  values = getDataCsv(file, start, end)
  pprint.pprint(values, width=200, depth=2)
  import myGSpread
  myGSpread.insertRows(values, "運用履歴", "data", 0)
  input("enter any key to exit")

