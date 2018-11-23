#
# Web server (not on AppEngine)
#

from flask import Flask, request

import myGmail
import myBigQuery
import myStock
import checkAlive
import sendJamInfoToBigQuery
import private

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)


@app.route("/")
@app.route("/"+private.project_app)
@app.route("/"+private.project_app+"/")
def hello():
    return 'Hello World! This page is created by AppEngine.'

@app.route("/sendJamInfo")
@app.route("/"+private.project_app+"/sendJamInfo")
def sendJamInfo():
    sendJamInfoToBigQuery.send()
    return 'done'

@app.route("/checkAlive")
@app.route("/"+private.project_app+"/checkAlive")
def doCheckAlive():
    s = checkAlive.checkAlive()
    return s

@app.route("/"+private.project_app+"/insertBQ")
def insertBQ():
    table = request.args.get('table', '')
    value1 = request.args.get('value1', '')
    value2 = request.args.get('value2', '')
    value3 = request.args.get('value3', '')
    value4 = request.args.get('value4', '')
    myBigQuery.triggerBigQuery(table, [[value1, value2, value3, value4]])
    import gc
    gc.collect()
    return 'done inserting to '+table+", ("+value1+", "+value2+", "+value3+", "+value4+")"

@app.route("/"+private.project_app+"/gmail")
def gmail():
    addr_to = request.args.get('to', '')
    subject = request.args.get('subject', '')
    body = request.args.get('body', '')
    if addr_to == "":
        addr_to = "sdkn104@yahoo.co.jp"
    myGmail.sendGmail("sdkn104home@gmail.com", addr_to, subject, body)
    return 'done sending gmail '+subject+" to "+addr_to

@app.route("/sendStock")
@app.route("/"+private.project_app+"/sendStock")
def sendStock():
    names_jp = ["1330", "9984", "1699", "6753"]
    names_bloom = ["USDJPY:CUR", "HKDJPY:CUR", "EURJPY:CUR", 
                   "VWO:US", "IYR:US", "IVV:US", "VNM:US",
                   "2836:HK"]
    myStock.sendToBQ(names_jp, names_bloom, "stock_rcv")
    return 'done'


@app.route("/"+private.project_app+"/gmail_test")
def gmail_test():
    myGmail.test()
    return 'sent'

@app.route("/"+private.project_app+"/test")
def test():
    return 'test'

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    import os
    import logging
    dirs = ["/home/sdkn104home/", "/home/sdkn104/system/log/","/home/sadakane/system/log/", "./"]
    for d in dirs:
       if os.path.exists(d):
          logdir = d
    print("set logdir to " + d)
    logging.basicConfig(filename=logdir+'flask.log',level=logging.INFO)
    #app.run(host='127.0.0.1', port=8080, debug=True)
    app.run(host='0.0.0.0', port=80, debug=True) #
