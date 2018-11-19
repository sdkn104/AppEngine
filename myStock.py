import re
import io
import datetime
import pandas as pd
import pandas_datareader.data as web
import requests
from bs4 import BeautifulSoup
import urllib.parse

import myBigQuery

def getDataIEX(names, start, end):
  # list: https://api.iextrading.com/1.0/ref-data/symbols
  df = web.DataReader(names, 'iex', start, end)
  dfs = []
  for n in names:
        d = df.xs(n,level=1, axis=1)
        d = d.assign(name=n)
        dfs.append(d)
        #print(d.head())
  dfall = pd.concat(dfs)
  dfall = dfall.reset_index().ix[:,["date","name","open","high","low","close","volume"]]
  return dfall

def getDataFX(start, end):
  df =  web.DataReader(["DEXHKUS","DEXUSEU","DEXJPUS"],"fred",start,end)
  df1 = df.assign(name="USDJPY", close=df["DEXJPUS"])
  df2 = df.assign(name="EURJPY", close=df["DEXJPUS"] * df["DEXUSEU"])
  df3 = df.assign(name="HKDJPY", close=df["DEXJPUS"] /df["DEXHKUS"])
  dfall = pd.concat([df1, df2, df3])
  dfall = dfall.reset_index()
  dfall = dfall.assign(open=0, high=0, low=0, volume=0, date=dfall["DATE"])
  dfall = dfall.ix[:,["date","name","open","high","low","close","volume"]]
  return dfall

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
        df = pd.DataFrame(data={"date":[today], "name":[name], "open":0, "high":0, "low":0, 
                                "close":[price], "volume":0})
        dfs.append(df)
    dfall = pd.concat(dfs)
    return dfall

def getDataJP(names, start, end):
    start_str = start.strftime("%Y-%m-%d")
    end_str   = end.strftime("%Y-%m-%d")
    dfs = []
    for name in names:
        url = "http://finance-web.info/download_historical/" + name
        r = requests.get(url)
        csv_io = io.StringIO(r.content.decode('shift-jis'))
        df = pd.read_csv(csv_io)
        df.columns = ["date", "y", "m", "d", "open", "high", "low", "close", "volume"]
        d = df["date"].astype(str)
        d = d.str[0:4] + "-" + d.str[4:6] + "-" + d.str[6:8]
        df = df.assign(date=d, name=name)
        df = df.ix[:,["date","name","open","high","low","close","volume"]]
        dfs.append(df)
    dfall = pd.concat(dfs)
    dfall = dfall[(dfall.date >= start_str) & (dfall.date <= end_str)]
    return dfall

def insertBQ(names_jp, names_bloom):
    #end = datetime.datetime(2018, 11, 14)
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=7)
    #names = ['GPL','AAPL']
    #df1 = getDataIEX(names, start, end)
    #df2 = getDataFX(start,end)
    df3 = getDataBloomberg(names_bloom)
    df4 = getDataJP(names_jp, start, end)
    df = pd.concat([df3, df4])
    #print(df.head())
    myBigQuery.loadBigQuery("stock_rcv", df.values)

if __name__ == "__main__":
    names_jp = ["1322","1323"]
    names_bloom = ["2836:HK","USDJPY:CUR","AAPL:US"]
    insertBQ(names_jp, names_bloom)

