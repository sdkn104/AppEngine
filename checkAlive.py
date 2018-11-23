#!/usr/bin/python3  
# coding: utf-8

import urllib.parse
import datetime
from google.cloud import bigquery
import os
#from google.appengine.api import mail
import urllib.request

import private
import myGmail

bqJsonPath = ["/home/sdkn104/system/etc/BigQueryKey.json","credentials/BigQueryKey.json"]
for json in bqJsonPath:
  if os.path.exists(json):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json
    print("BigQuery key file = " + json)

def checkAliveFor(devName, maxInterval, timeFormat, sql):
    client = bigquery.Client()
    query_job = client.query(sql)

    results = query_job.result()  # Waits for job to complete.
    last = ""
    for r in results:
        last = r.TIME
    JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
    dtlast = datetime.datetime.strptime(last, timeFormat).replace(tzinfo=JST)
    #print(dtlast)
    dtnow = getNowJST()
    #print(dtnow)
    #print(dtlast + datetime.timedelta(seconds=maxInterval))
    if( dtnow > dtlast + datetime.timedelta(seconds=maxInterval) ):
        print("error: "+devName)
        sendAlertMail(devName, str(dtlast))
        chk = "ng"
    else:
        chk = "ok"
    #assert errors == []  # exception occur, so response status >= 300
    
    s = "%s: %s, now %s, last %s, interval %d sec." % (devName, chk, str(dtnow), str(dtlast), maxInterval)
    print(s)
    return s+"\n"

def getNowJST():
    JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
    dt = datetime.datetime.now(JST)
    return dt

def sendAlertMail(devName, lastTime):
    #triggerIFTTT("NotAlive", devName, str(getNowJST()), lastTime)
    msg = myGmail.sendAlertMail( \
                "Not Alive, "+devName, "Not Alive "+devName+"\nnow:  "+str(getNowJST())+"\nlast: "+lastTime)


#def triggerIFTTT(event, value1, value2, value3):
#    key = "uoVHdqccPNfLG8UbUR6Al"
#    url = "http://maker.ifttt.com/trigger/"+urllib.parse.quote(event)+"/with/key/"+key + \
#          "?value1="+urllib.parse.quote(value1)+"&value2="+urllib.parse.quote(value2)+ \
#          "&value3="+urllib.parse.quote(value3)  #+" HTTP/1.1\r\n"
#    #print(url)
#    res = urllib.request.urlopen(url)
#    status = res.getcode()
#    #print(status)
#    #print(res.read())

#from memory_profiler import profile
#@profile
def checkAlive():
    s = ""
    s += checkAliveFor("basic", 3600, "%Y-%m-%d %H:%M:%S JST", 
            "SELECT MAX(DATA_TIME) as TIME FROM `"+private.project_id+".HOME_IoT.basic_rcv`")
    s += checkAliveFor("espnow3", 3600, "%Y-%m-%d %H:%M:%S JST",
            "SELECT MAX(DATA_TIME) as TIME FROM `"+private.project_id+".HOME_IoT.espnow3_rcv`")
    s += checkAliveFor("espnow5", 3600, "%Y-%m-%d %H:%M:%S JST",
            "SELECT MAX(DATA_TIME) as TIME FROM `"+private.project_id+".HOME_IoT.espnow5_rcv`")
    s += checkAliveFor("jam", 3600, "%Y-%m-%d %H:%M:%S JST",
            "SELECT MAX(SEND_TIME) as TIME FROM `"+private.project_id+".HOME_IoT.jam_rcv`")
    s += checkAliveFor("orangepi", 3600, "%Y-%m-%d %H:%M:%S JST",
            "SELECT MAX(TIME) as TIME FROM `"+private.project_id+".HOME_IoT.device_heartbeat` WHERE DEVICE = 'orangepione'")
    return s


if __name__ == '__main__':
    checkAlive()

