import re
import io
import datetime
import requests
from bs4 import BeautifulSoup
import urllib.parse
import csv


#from memory_profiler import profile
#@profile
#def test():
#  return 1
#test()

def getDataIEX(names, start, end):
  # list: https://api.iextrading.com/1.0/ref-data/symbols
  import pandas as pd  # require about 60MB memory
  import pandas_datareader.data as web
  df = web.DataReader(names, 'iex', start, end)
  dfs = []
  for n in names:
        d = df.xs(n,level=1, axis=1)
        d = d.assign(name=n)
        dfs.append(d)
        #print(d.head())
  dfall = pd.concat(dfs)
  dfall = dfall.reset_index().ix[:,["date","name","open","high","low","close","volume"]]
  return dfall.values

def getDataFX(start, end):
  import pandas as pd  # require about 60MB memory
  import pandas_datareader.data as web
  df =  web.DataReader(["DEXHKUS","DEXUSEU","DEXJPUS"],"fred",start,end)
  df1 = df.assign(name="USDJPY", close=df["DEXJPUS"])
  df2 = df.assign(name="EURJPY", close=df["DEXJPUS"] * df["DEXUSEU"])
  df3 = df.assign(name="HKDJPY", close=df["DEXJPUS"] /df["DEXHKUS"])
  dfall = pd.concat([df1, df2, df3])
  dfall = dfall.reset_index()
  dfall = dfall.assign(open=0, high=0, low=0, volume=0, date=dfall["DATE"])
  dfall = dfall.ix[:,["date","name","open","high","low","close","volume"]]
  return dfall.values

def getDataBloomberg(names):
    dfs = []
    for name in names:
        url = "https://www.bloomberg.co.jp/quote/"+name
        r = requests.get(url)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        soup = BeautifulSoup(r.content, "html.parser")
        price = soup.select("div.price")[0].text.strip()
        ticker = soup.select("div.ticker")[0].text.strip()
        date = soup.select("div.price-datetime")[0].text.strip()
        #print([today, price, ticker, date])
        assert ticker == name
        d=[today, name, 0, 0, 0, price, 0]
        dfs.append(d)
    return dfs

def getDataJP(names, start, end):
    start_str = start.strftime("%Y-%m-%d")
    end_str   = end.strftime("%Y-%m-%d")
    mat_all = []
    for name in names:
        url = "http://finance-web.info/download_historical/" + name
        r = requests.get(url)
        csv_io = io.StringIO(r.content.decode('shift-jis'), newline='')
        csvReader = csv.reader(csv_io)
        mat = [row for row in csvReader]
        del mat[0]  # delete header
        # ["date", "y", "m", "d", "open", "high", "low", "close", "volume"]
        for row in mat:
            del row[2:4] # delete m and d columns
            #print(row)
            row[0] = row[0][0:4] + "-" + row[0][4:6] + "-" + row[0][6:8] # create yyyy-mm-dd
            row[1] = name
        mat = [row for row in mat if (row[0]  >= start_str) and (row[0] <= end_str) ]
        assert len(mat) > 0
        mat_all.extend(mat)
    return mat_all

def sendToBQ(names_jp, names_bloom, table):
    import myBigQuery
    try:
        #end = datetime.datetime(2018, 11, 14)
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        #names = ['GPL','AAPL']
        #mat3 = getDataIEX(names, start, end)
        #mat4 = getDataFX(start,end)
        mat1 = getDataBloomberg(names_bloom)
        mat2 = getDataJP(names_jp, start, end)
        mat = mat1 + mat2
        #print(mat)
        myBigQuery.loadBigQuery(table, mat)
    except Exception as e:
        import myGmail
        import traceback
        tb = traceback.format_exc()
        #print("traceback:\n"+tb)
        print("error (%s) caught. sending Mail." % type(e))
        msg = "Failed to send stock info to BigQuery by myStock.sendToBQ().\ntrace:\n"+tb
        myGmail.sendGmail("sdkn104home@gmail.com", "sdkn104@gmail.com;sdkn104@yahoo.co.jp", 
                          "ERROR on myStock", msg)
        raise


if __name__ == "__main__":
    names_jp = ["1322","1323"]
    names_bloom = ["2836:HK","USDJPY:CUR","AAPL:US"]
    sendToBQ(names_jp, names_bloom, "stock_rcv")

