import re
import io
import os
import datetime
import pprint
import chardet

#from memory_profiler import profile
#@profile
#def test():
#  return 1
#test()

def tofloat(s):
  return float(re.sub(r"^\s*$","0",str(s)).replace(",",""))

def datefmt(s):
  m = re.search(r'^\s*(\d+)[/-](\d+)[/-](\d+)',s)
  y = m.group(1) if len(m.group(1))==4 else "20"+m.group(1)
  return "%s-%02d-%02d" % (y, int(m.group(2)), int(m.group(3)))

# read CSV and retern list of lists
def getDataCsv(csvfile, start=datetime.datetime(1900,1,1), end=datetime.datetime(2999,12,31)):
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
  print("".join(lines).replace('"',''))
  print("read csv %d lines" % len(lines))
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
      p = row["受渡金額［USドル］"] if row["受渡金額［USドル］"] != "-" else row["約定代金［USドル］"]
      paid = tofloat(p) * sign * float(rate)
      code = row["ティッカー"]
      comment = "%s USDrate=%g" % (code, rate)
      mat.append([date, name, account, paid, amount, price, comment])
      name = "USDJPY"
      amount = tofloat(p) * sign * -1
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

# read HTML file/text 
def getDataHtml(html):
  from bs4 import BeautifulSoup
  # read file or string
  if os.path.exists(html):
    with open(html, "rb") as f:
      enc = chardet.detect(f.read())["encoding"]
    with open(html, "r", encoding=enc) as f:
      html_str = f.read()
  else:
    html_str = html

  soup = BeautifulSoup(html_str, "html.parser")
  tbl = None
  type = ""
  # gaitame
  for t in soup.find_all("table"):
    c = t.find_all("div",attrs={"class":["uforex1_class_bid_img","uforex1_class_ask_img"]})
    if len(c) > 0:
        tbl = t
        type = "gaitame"
  # click365
  if tbl is None:
    tbl = soup.find("table", id="executeList")
    type = "click365"

  rows = tbl.find_all("tr")

  mat = []
  if type == "gaitame":
    for row in rows:
      csvRow = []
      for cell in row.select("td, th"):
        if cell.find_all(attrs={"class":"uforex1_class_bid_img"}):
          txt = "売"
        elif cell.find_all(attrs={"class":"uforex1_class_ask_img"}):
          txt = "買"
        else:
          txt = cell.get_text()
        csvRow.append(txt)
      print(csvRow)
      if len(csvRow) == 13:
        kubun = csvRow[3]
        date = datefmt(csvRow[0]) if kubun == "決済約定" else datefmt(csvRow[6]) if kubun == "新規約定" else "err"
        name = csvRow[2]
        sign = 1 if csvRow[4]=="買" else -1 if csvRow[4]=="売" else 0
        amount = tofloat(csvRow[5]) * 1000 * sign 
        sinki_price = tofloat(csvRow[7])
        kessai_price = tofloat(csvRow[8])
        price = kessai_price if kubun == "決済約定" else sinki_price if kubun == "新規約定" else 0
        tesuryo = tofloat(csvRow[9])
        swap = tofloat(csvRow[10])
        paid = price * amount + tesuryo + swap
        account = "外為NEXT"
        comment = "SWAP:"+str(swap)
        mat.append([date, name, account, paid, amount, price, comment])
  else:
    for row in rows:
      csvRow = []
      for cell in row.select("td, th"):
        txt = cell.get_text()
        csvRow.append(txt)
      print(csvRow)
      if len(csvRow) >= 10:
        date = datefmt(csvRow[3])
        name = csvRow[6].replace("\n","")
        account = "クリック株365"
        sign = 1 if "買" in csvRow[8] else -1 if "売" in csvRow[8] else 0
        amount = tofloat(csvRow[10]) * 100 * sign
        price = tofloat(csvRow[11])
        kinri_haito = tofloat(csvRow[13])
        tesuryo = tofloat(csvRow[14])
        paid = price * amount + tesuryo + kinri_haito
        comment = "金利/配当:"+str(kinri_haito)
        mat.append([date, name, account, paid, amount, price, comment])

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
  print("sending %d records..." % len(values))
  import myGSpread
  myGSpread.insertRows(values, "運用履歴", "data", 0)
  input("enter any key to exit")

